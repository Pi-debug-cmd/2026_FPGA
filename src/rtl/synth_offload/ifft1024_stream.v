`timescale 1ns/1ps
// ============================================================================
// WORLD 合成卸载（增量 1）：流式 1024 点 IFFT 核（时分复用 / 资源收敛版）
//
// 功能：每帧接收 513 个复数频点 X[0..512]（DC..Nyquist），内部按厄米对称补齐
//       X[1024-k] = conj(X[k])（k=1..511），做 1024 点逆 DFT：
//           x[n] = (1/1024) * sum_{k=0..1023} X[k] * exp(+j*2*pi*k*n/1024)
//       输出 1024 个时域实样本（虚部由厄米对称保证为 0，不输出）。
//
// 接口（AXI-Stream 风格 valid/ready 背压）：
//   s_axis_tdata[15:0]  = real_q15  （Q1.15 有符号）
//   s_axis_tdata[31:16] = imag_q15  （Q1.15 有符号）
//   输入固定 513 拍，k = 0..512 顺序；s_axis_tlast 预留，本版本忽略（按拍计数）。
//   s_axis_tready 仅在空闲态为 1；一帧处理期间为 0（上游需缓存/等待）。
//   m_axis_tdata[17:0]  = x[n] Q1.17，tdata[31:18] 为符号扩展。
//   m_axis_tlast 在 n = 1023 时为 1。输出在 m_axis_tready=0 时保持稳定。
//
// 定点格式（与 gen_ifft_vectors.py 的定点模型逐位一致）：
//   输入 Q1.15；内部/输出 Q1.17（18 位有符号）；旋转因子 Q3.15（18 位有符号，
//   1.0=32768）；每级蝶形缩放 1/2（10 级共 1/1024，等价 numpy ifft），逐级缩放
//   保证内部不溢出。复数乘：18x18 -> 36 位，加 2^14 四舍五入后右移 15 位，
//   饱和到 18 位；和/差为 19 位，加 1 后算术右移 1 位（四舍五入）。
//
// 输入无溢出契约（主机侧保证）：
//   (|X[0]| + |X[512]| + 2*sum_{k=1..511}|X[k]|) / 1024 <= 0.99
//   且 |X[k]| <= 32767/32768（Q1.15 不削顶）。
//
// 结构（时分复用，2026-10-18 资源收敛版）：
//   - 1 个 radix-2 蝶形，串行完成 10 级 x 512 次 = 5120 次蝶形；
//   - 1 块 1024x36 单读单写 SDP BRAM（dpram_1024x36.v，1 个 RAMB36 = 2 个 RAMB18）；
//   - 1 个 512x36 旋转因子 ROM（Q3.15，1 个 RAMB18）；
//   - 4 个 DSP 做复数乘（18x18）。
//   每次蝶形 6 拍：读 A / 读 B / 4 乘打拍 / 和差舍入 / 写 A / 写 B。
//   每帧约 33.3k 拍 = 333 us @100 MHz -> 约 3000 帧/s，是 WORLD 需求
//   （100 帧/s）的约 30 倍，时分复用余量充足。
// ============================================================================
module ifft1024_stream (
    input  wire        clk,
    input  wire        rst_n,          // 同步复位，低有效
    // 频域输入（513 点复数谱）
    input  wire        s_axis_tvalid,
    output wire        s_axis_tready,
    input  wire [31:0] s_axis_tdata,   // {imag_q15[15:0], real_q15[15:0]}
    input  wire        s_axis_tlast,   // 预留，本版本忽略
    // 时域输出（1024 点实样本）
    output wire        m_axis_tvalid,
    input  wire        m_axis_tready,
    output wire [31:0] m_axis_tdata,   // {{14{x[17]}}, x[17:0]}（Q1.17）
    output wire        m_axis_tlast,
    output wire        busy,           // 1 = 正在处理一帧
    output reg         done            // 一帧结束脉冲（1 拍）
);
    localparam [3:0] S_IDLE  = 4'd0,   // 空闲，可接收输入
                     S_WA    = 4'd1,   // 写 X[k] 到 mem[rev(k)]
                     S_WB    = 4'd2,   // 写 conj(X[k]) 到 mem[rev(1024-k)]
                     S_START = 4'd3,   // 初始化蝶形计数
                     S_BR1   = 4'd4,   // 蝶形 1/6：读 A
                     S_BR2   = 4'd5,   // 蝶形 2/6：读 B，同时锁存 A
                     S_BMUL  = 4'd6,   // 蝶形 3/6：4 个乘积打拍
                     S_BADD  = 4'd7,   // 蝶形 4/6：和/差 + 舍入 + 饱和
                     S_BWA   = 4'd8,   // 蝶形 5/6：计算并写回 A
                     S_BWB   = 4'd9,   // 蝶形 6/6：计算并写回 B，推进计数
                     S_OUT   = 4'd10,  // 输出 1024 点
                     S_DONE  = 4'd11;  // 结束脉冲

    localparam [9:0] LAST_BIN   = 10'd512;   // 最后一个输入频点
    localparam [3:0] LAST_STAGE = 4'd10;     // 1024 = 2^10

    // ------------------------------------------------------------------
    // 寄存器声明
    // ------------------------------------------------------------------
    reg [3:0]  state;
    reg [9:0]  in_count;      // 已接收频点计数 0..512
    reg [3:0]  stage;         // 当前蝶形级 1..10
    reg [9:0]  bf_count;      // 当前级内蝶形序号 0..511
    reg [10:0] out_count;     // 输出序号 0..1024
    reg [9:0]  out_raddr;     // 输出读地址（只在发起新读时前进，保证背压下数据稳定）
    reg        m_valid_r;     // 输出 valid 寄存器
    reg [15:0] in_re, in_im;  // 输入频点锁存（Q1.15）

    // 蝶形中间寄存器
    reg signed [17:0] u_re, u_im;                  // A 点（被减/加的那一路）
    reg signed [35:0] pr_rr, pr_ri, pr_ir, pr_ii;   // 4 个乘积打拍
    reg signed [17:0] t_re, t_im;                  // B * w，Q1.17
    reg [35:0] q_tw;                               // 旋转因子 ROM 读数据

    // 数据缓冲读数据
    wire [35:0] dout;

    // ------------------------------------------------------------------
    // 定点工具函数
    // ------------------------------------------------------------------
    // 10 位下标按位倒序：DIT 前把输入按倒序装载，10 级后即得自然序输出
    function [9:0] rev10;
        input [9:0] v;
        begin
            rev10 = {v[0], v[1], v[2], v[3], v[4],
                     v[5], v[6], v[7], v[8], v[9]};
        end
    endfunction

    // 21 位中间值饱和到 18 位 Q1.17（正常数据不触发，用于防御）
    function signed [17:0] sat18;
        input signed [20:0] v;
        begin
            if (v > 21'sd131071)
                sat18 = 18'sd131071;
            else if (v < -21'sd131072)
                sat18 = -18'sd131072;
            else
                sat18 = v[17:0];
        end
    endfunction

    // ------------------------------------------------------------------
    // 输入 Q1.15 -> 内部 Q1.17（左移 2 位；-32768 得到 -131072，18 位补码可表示）
    // ------------------------------------------------------------------
    wire signed [17:0] xa_re = {in_re, 2'b00};
    wire signed [17:0] xa_im = {in_im, 2'b00};
    wire signed [17:0] xa_im_conj = -xa_im;
    wire [9:0] inv_count = 10'd0 - in_count;   // 1024-in_count（k=1..511 时有效）

    // ------------------------------------------------------------------
    // 蝶形地址与旋转因子地址（组合逻辑，由 stage/bf_count 决定）
    // ------------------------------------------------------------------
    wire [9:0] bf_half  = 10'd1 << (stage - 4'd1);
    wire [9:0] bf_j     = bf_count & (bf_half - 10'd1);
    wire [9:0] bf_group = bf_count >> (stage - 4'd1);
    wire [9:0] bf_a     = (bf_group << stage) | bf_j;
    wire [9:0] bf_b     = bf_a | bf_half;
    wire [9:0] tw_word  = bf_j << (4'd10 - stage);
    wire [8:0] tw_addr  = tw_word[8:0];

    // 输出阶段是否发起新的读（被 tready 挡住时保持地址与数据）
    wire out_issue = (state == S_OUT) && (out_count != 11'd1024) &&
                     (!m_valid_r || m_axis_tready);

    // ------------------------------------------------------------------
    // 复数乘（S_BMUL：dout=B、q_tw=w，把 4 个乘积打拍）
    // ------------------------------------------------------------------
    wire signed [17:0] v_re = dout[17:0];
    wire signed [17:0] v_im = dout[35:18];
    wire signed [17:0] w_re = q_tw[17:0];
    wire signed [17:0] w_im = q_tw[35:18];

    // ------------------------------------------------------------------
    // 和/差 + 舍入 + 饱和（S_BADD 组合计算并寄存 t_re/t_im）
    // ------------------------------------------------------------------
    wire signed [36:0] acc_re = {{1{pr_rr[35]}}, pr_rr} - {{1{pr_ri[35]}}, pr_ri};
    wire signed [36:0] acc_im = {{1{pr_ir[35]}}, pr_ir} + {{1{pr_ii[35]}}, pr_ii};
    // 加 2^14 后算术右移 15 位（Q4.32 -> Q4.17，四舍五入），再饱和到 18 位
    wire signed [20:0] t_re_raw = (acc_re + 37'sd16384) >>> 15;
    wire signed [20:0] t_im_raw = (acc_im + 37'sd16384) >>> 15;

    // ------------------------------------------------------------------
    // 和/差 + 1/2 缩放（S_BWA / S_BWB 计算）
    // ------------------------------------------------------------------
    wire signed [18:0] sum_re = {u_re[17], u_re} + {t_re[17], t_re} + 19'sd1;
    wire signed [18:0] sum_im = {u_im[17], u_im} + {t_im[17], t_im} + 19'sd1;
    wire signed [18:0] dif_re = {u_re[17], u_re} - {t_re[17], t_re} + 19'sd1;
    wire signed [18:0] dif_im = {u_im[17], u_im} - {t_im[17], t_im} + 19'sd1;
    // (u +/- t)/2：19 位算术右移 1 位即 sum[18:1]，结果必然落在 18 位范围内
    wire signed [17:0] out_a_re = sum_re[18:1];
    wire signed [17:0] out_a_im = sum_im[18:1];
    wire signed [17:0] out_b_re = dif_re[18:1];
    wire signed [17:0] out_b_im = dif_im[18:1];

    // ------------------------------------------------------------------
    // 数据缓冲端口（1 读 1 写，SDP）
    // ------------------------------------------------------------------
    wire        mem_we;
    wire [9:0]  mem_waddr;
    wire [35:0] mem_wdata;
    wire [9:0]  mem_raddr;

    assign mem_we    = (state == S_WA) || (state == S_WB) ||
                       (state == S_BWA) || (state == S_BWB);
    assign mem_waddr = (state == S_WA) ? rev10(in_count)
                     : (state == S_WB) ? rev10(inv_count)
                     : (state == S_BWA) ? bf_a : bf_b;
    assign mem_wdata = (state == S_WB) ? {xa_im_conj, xa_re}
                     : (state == S_BWA) ? {out_a_im, out_a_re}
                     : (state == S_BWB) ? {out_b_im, out_b_re}
                     : {xa_im, xa_re};
    // 读地址：输出阶段按 out_raddr（发起新读时读下一格），蝶形阶段读 A/B
    assign mem_raddr = (state == S_OUT)
                     ? (out_issue ? (out_raddr + 10'd1) : out_raddr)
                     : ((state == S_BR1) ? bf_a : bf_b);

    dpram_1024x36 u_buf (
        .clk   (clk),
        .we    (mem_we),
        .waddr (mem_waddr),
        .wdata (mem_wdata),
        .raddr (mem_raddr),
        .dout  (dout)
    );

    // ------------------------------------------------------------------
    // 旋转因子 ROM（512 项 Q3.15，地址 = j * 1024/len；1 个 RAMB18）
    // ------------------------------------------------------------------
    twiddle_rom_1024 u_rom (
        .clk  (clk),
        .addr (tw_addr),
        .data (q_tw)
    );

    // ------------------------------------------------------------------
    // 主状态机
    // ------------------------------------------------------------------
    assign s_axis_tready = rst_n && (state == S_IDLE);
    assign busy          = (state != S_IDLE);
    assign m_axis_tvalid = m_valid_r;
    assign m_axis_tdata  = {{14{dout[17]}}, dout[17:0]};
    assign m_axis_tlast  = m_valid_r && (out_count == 11'd1024);

    always @(posedge clk) begin
        if (!rst_n) begin
            state     <= S_IDLE;
            in_count  <= 10'd0;
            stage     <= 4'd1;
            bf_count  <= 10'd0;
            out_count <= 11'd0;
            out_raddr <= 10'd1023;   // 哨兵：首次发起读时 +1 得 0
            m_valid_r <= 1'b0;
            in_re     <= 16'd0;
            in_im     <= 16'd0;
            u_re      <= 18'sd0;
            u_im      <= 18'sd0;
            t_re      <= 18'sd0;
            t_im      <= 18'sd0;
            pr_rr     <= 36'sd0;
            pr_ri     <= 36'sd0;
            pr_ir     <= 36'sd0;
            pr_ii     <= 36'sd0;
            done      <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                // 接收一个频点（Q1.15 打包在 32 位 tdata 中）
                S_IDLE: if (s_axis_tvalid) begin
                    in_re <= s_axis_tdata[15:0];
                    in_im <= s_axis_tdata[31:16];
                    state <= S_WA;
                end

                // 写自然序频点到倒序地址（k=0 无共轭伙伴）
                S_WA: begin
                    if (in_count == LAST_BIN) begin
                        state <= S_START;          // 收满 513 点，启动 FFT
                    end else if (in_count == 10'd0) begin
                        in_count <= in_count + 10'd1;
                        state    <= S_IDLE;
                    end else begin
                        state <= S_WB;             // 1..511 需要写共轭点
                    end
                end

                // 写共轭点 X[1024-k] = conj(X[k])
                S_WB: begin
                    in_count <= in_count + 10'd1;
                    state    <= S_IDLE;
                end

                // 初始化蝶形计数
                S_START: begin
                    stage    <= 4'd1;
                    bf_count <= 10'd0;
                    state    <= S_BR1;
                end

                // 蝶形 1/6：读 A（同步读，下一拍 dout=A）
                S_BR1: state <= S_BR2;

                // 蝶形 2/6：读 B，同时把 A 锁存到 u_re/u_im
                S_BR2: begin
                    u_re  <= dout[17:0];
                    u_im  <= dout[35:18];
                    state <= S_BMUL;
                end

                // 蝶形 3/6：4 个 18x18 乘积打拍（DSP 输出寄存，缩短组合路径）
                S_BMUL: begin
                    pr_rr <= v_re * w_re;
                    pr_ri <= v_im * w_im;
                    pr_ir <= v_re * w_im;
                    pr_ii <= v_im * w_re;
                    state <= S_BADD;
                end

                // 蝶形 4/6：和/差 + 舍入 + 饱和
                S_BADD: begin
                    t_re  <= sat18(t_re_raw);
                    t_im  <= sat18(t_im_raw);
                    state <= S_BWA;
                end

                // 蝶形 5/6：计算 (u+t)/2 并写回 A
                S_BWA: state <= S_BWB;

                // 蝶形 6/6：计算 (u-t)/2 并写回 B，推进级/蝶形计数
                S_BWB: begin
                    if (bf_count == 10'd511) begin
                        bf_count <= 10'd0;
                        if (stage == LAST_STAGE) begin
                            out_count <= 11'd0;
                            out_raddr <= 10'd1023;
                            state     <= S_OUT;
                        end else begin
                            stage <= stage + 4'd1;
                            state <= S_BR1;
                        end
                    end else begin
                        bf_count <= bf_count + 10'd1;
                        state    <= S_BR1;
                    end
                end

                // 顺序输出 1024 个实样本；valid 在 tready 为 0 时保持。
                // out_raddr/out_count 只在真正发起新读时前进，被背压挡住时
                // 读地址保持不变，因此 dout、tdata、tlast 都保持稳定。
                S_OUT: begin
                    if (out_issue) begin
                        out_count <= out_count + 11'd1;
                        out_raddr <= out_raddr + 10'd1;
                        m_valid_r <= 1'b1;
                    end
                    if (m_valid_r && m_axis_tready && (out_count == 11'd1024)) begin
                        m_valid_r <= 1'b0;
                        state     <= S_DONE;
                    end
                end

                // 一帧结束脉冲，回到空闲
                S_DONE: begin
                    done  <= 1'b1;
                    state <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end
endmodule

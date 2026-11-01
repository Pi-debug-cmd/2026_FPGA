`timescale 1ns/1ps
// ============================================================================
// WORLD 最小相位加速器 · 复数 exp 单元（PL-EXP2-20261022 时序修复版）
//
// 功能：对 513 个 bin 计算 y = exp(a) * (cos b, sin b)
//   输入 a = log_spectrum/1024（Q5.18，24 位有符号）
//        b = im/1024（Q5.18，24 位有符号；<0 时内部 +2π 归一到 [0,2π)）
//   输出 y_re/y_im Q2.17（20 位有符号，覆盖 |y|max≈1.115，不削顶）
//
// 与 Python 定点模型（build/generated/pl_synth_offload/cpu_breakdown/gen_exp_vectors.py）逐位一致：
//   K  = (A*94548) >>> 34                      # floor(a/ln2)
//   R  = A - K*181704（越界时 ±ln2 修正 K）
//   IDX= (R*94548) >>> 26 ; FRAC = (R*94548)[25:10]
//   E_Q16 = EXP[IDX] + ((EXP[IDX+1]-EXP[IDX])*FRAC >>> 16)      # EXP[256]=2*EXP[0]
//   E_Q17 = SH>=0 ? E_Q16>>>SH : E_Q16<<(-SH), SH=-(K+1)
//   J  = (B_N*41722) >>> 26 ; F = (B_N*41722)[25:10]
//   COS/SIN = LUT[J] + (((LUT[(J+1)&1023]-LUT[J])*F) >>> 16)
//   Y_RE = (E_Q17*COS + 2^17) >>> 17（Y_IM 同理），饱和到 20 位
//
// 2026-10-22 PL-EXP-20261022：功能修复（cos/sin 插值位宽/符号、exp ROM 成对存储、
//   流水对齐、+2^17 舍入常数），xsim 49248 bin 0 LSB PASS。
//
// 2026-10-22 PL-EXP2-20261022：100 MHz 时序修复。OOC 综合 WNS=-2.511 ns，关键路径
//   u_rom/exp_lo_reg[0]/C -> yim_rnd/A[7] 数据路径 12.140 ns / 18 级逻辑：
//   exp ROM 输出 -> exp_dif 减法 -> exp 乘法 DSP(A->P 3.375ns) -> e_q16 加法 ->
//   e_q17 可变移位 -> 最终复数乘 DSP 输入，全部挤在一个组合段内。
//   现把整条链路切成 13 拍/bin 流水，每拍最多 1 次 DSP 乘 + 少量小位宽逻辑：
//     S_IDLE  拍1：收输入
//     S_K     拍2：k0 = (A*94548)>>>34                      [DSP 乘]
//     S_R0    拍3：R0 = A - k0*181704                       [DSP 乘 + 减法]
//     S_RC    拍4：R0 越界修正 -> R,K；B 归一 -> B_N        [小位宽加/减]
//     S_ADDR  拍5：idx/frac=(R*94548)；j/f=(B_N*41722)      [两路 DSP 乘]
//     S_ROMA  拍6：给 ROM 地址 idx/j（exp 成对表 + LUT[j]）
//     S_ROMB  拍7：寄存 exp_dif=hi-lo、LO、LUT[j]，角度地址切 j+1
//     S_EXPM  拍8：exp 乘 frac；cos/sin 差值 = LUT[j+1]-LUT[j]   [DSP 乘]
//     S_EQ16  拍9：e_q16 = LO + (prod>>>16)；cos/sin 乘 F         [DSP 乘]
//     S_EQ17 拍10：e_q17 = e_q16 按 SH 移位；cos/sin = LUT[j]+插值
//     S_MUL  拍11：y_re/y_im = e_q17 * cos/sin                   [DSP 乘 ×2]
//     S_RND  拍12：(prod + 2^17)>>>17 后饱和到 20 位
//     S_OUT  拍13：valid/ready 握手，帧尾 done
//   每帧 513×13 = 6669 拍；@100 MHz = 66.69 µs/帧（10 ms 帧预算的 0.667%，
//   远低于 100k 拍/帧上限；按 400 次/s 调用则占空比 ≈2.67%）。
//   时序意图：每拍只有 1 个 DSP48E1 A->P 组合段（约 3.4 ns）或若干 20~40 位
//   加减/移位（约 2~5 ns），不再存在 12 ns 长组合链。
//
// AXI-Stream：513 拍进 / 513 拍出；tdata 打包：输入 [23:0]=A、[47:24]=B；
// 输出 [19:0]=Y_RE、[39:20]=Y_IM。valid/ready 背压。
// 资源（相对上一版估算）：DSP48E1 仍 9 个、cos/sin ROM 1 RAMB36、exp 成对 ROM 综合为
// LUT ROM（约 250 LUT，未占 BRAM）；新增流水寄存器约 +380 FF（总 FF 约 550），
// LUT 约 480–560。均远低于预算（LUT≤8k、FF≤10k、DSP≤16）。
// ============================================================================
module minphase_exp_unit (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        s_axis_tvalid,
    output wire        s_axis_tready,
    input  wire [63:0] s_axis_tdata,   // [23:0]=A, [47:24]=B
    input  wire        s_axis_tlast,
    output wire        m_axis_tvalid,
    input  wire        m_axis_tready,
    output wire [63:0] m_axis_tdata,   // [19:0]=Y_RE, [39:20]=Y_IM
    output wire        m_axis_tlast,
    output wire        busy,
    output reg         done
);
    // 13 拍/bin 流水线（原 7 拍；每拍最多 1 次 DSP 乘 + 小位宽逻辑）
    localparam [3:0] S_IDLE = 4'd0,  S_K    = 4'd1,  S_R0   = 4'd2,
                     S_RC   = 4'd3,  S_ADDR = 4'd4,  S_ROMA = 4'd5,
                     S_ROMB = 4'd6,  S_EXPM = 4'd7,  S_EQ16 = 4'd8,
                     S_EQ17 = 4'd9,  S_MUL  = 4'd10, S_RND  = 4'd11,
                     S_OUT  = 4'd12;

    // 定点常数（与 gen_exp_vectors.py 完全一致）
    localparam signed [23:0] INV_LN2_Q16 = 24'sd94548;   // round(2^16/ln2)；同时是 exp 插值斜率
    localparam signed [24:0] LN2_Q18     = 25'sd181704;  // round(ln2*2^18)
    localparam signed [24:0] TWO_PI_Q18  = 25'sd1647099; // round(2π*2^18)
    localparam signed [24:0] INV_ANG     = 25'sd41722;   // round(1024/(2π*2^18)*2^26)
    localparam signed [20:0] RND_Q17     = 21'sd131072;  // 模型里的 +2^17 舍入项

    reg [3:0]  state;
    reg signed [23:0] a_r, b_r;
    reg [9:0]  bin_cnt;          // 0..512，帧长固定 513 bin
    reg        last_r;           // s_axis_tlast 寄存（帧长仍按 513 计数）
    reg        m_valid_r, m_last_r;
    reg signed [19:0] y_re_r, y_im_r;

    // ---- 流水寄存器（每级之间显式切分，避免长组合链） ----
    reg signed [7:0]  k0_r;      // S_K   -> K=floor(A/ln2)
    reg signed [24:0] r0_r;      // S_R0  -> R0 = A - K*ln2
    reg signed [7:0]  k_r;       // S_RC  -> 修正后的 K
    reg signed [23:0] r_r;       // S_RC  -> 修正后的 R
    reg signed [24:0] bn_r;      // S_RC  -> B<0 时 +2π 归一
    reg [7:0]  idx_r;
    reg [15:0] frac_r;
    reg [9:0]  j_r;
    reg [15:0] f_r;
    reg signed [5:0] sh_r;       // SH = -(K+1)

    wire [17:0] exp_lo, exp_hi;              // 成对 exp ROM：{e_{idx+1}, e_idx}
    wire signed [17:0] cos_q, sin_q;
    reg  signed [20:0] exp_dif_r;            // S_ROMB
    reg        [17:0] exp_lo_d;              // S_ROMB
    reg  signed [17:0] cos_l_r, sin_l_r;     // S_ROMB：LUT[j]
    reg  signed [17:0] cos_l_d, sin_l_d;     // S_EXPM：LUT[j] 延迟
    reg  signed [36:0] exp_prod_r;           // S_EXPM
    reg  signed [18:0] cos_dif_r, sin_dif_r; // S_EXPM：LUT[j+1]-LUT[j]
    reg  signed [23:0] e_q16_r;              // S_EQ16
    reg  signed [34:0] cos_prod_r, sin_prod_r;// S_EQ16
    reg  signed [20:0] e_q17_r;              // S_EQ17
    reg  signed [17:0] cos_r, sin_r;         // S_EQ17：插值结果
    reg  signed [38:0] yre_full_r, yim_full_r; // S_MUL

    // ---------------- S_K：K0 = (A*94548) >>> 34 ----------------
    wire signed [41:0] k_prod = a_r * INV_LN2_Q16;
    wire signed [7:0]  k0_c   = k_prod >>> 34;

    // ---------------- S_R0：R0 = A - K0*ln2 ----------------
    wire signed [24:0] a_ext = {a_r[23], a_r};
    wire signed [24:0] kln2  = k0_r * LN2_Q18;
    wire signed [24:0] r0_c  = a_ext - kln2;

    // ---------------- S_RC：R0 越界修正 + B 归一 ----------------
    wire signed [24:0] r1_c = (r0_r < 0) ? (r0_r + LN2_Q18) : r0_r;
    wire signed [7:0]  k1_c = (r0_r < 0) ? (k0_r - 8'sd1) : k0_r;
    wire signed [24:0] r2_c = (r1_c >= LN2_Q18) ? (r1_c - LN2_Q18) : r1_c;
    wire signed [7:0]  k2_c = (r1_c >= LN2_Q18) ? (k1_c + 8'sd1) : k1_c;
    wire signed [24:0] bn_c = b_r[23] ? ({b_r[23], b_r} + TWO_PI_Q18)
                                      :  {b_r[23], b_r};

    // ---------------- S_ADDR：exp/角度的 LUT 地址与小数 ----------------
    wire signed [41:0] u_prod = r_r * INV_LN2_Q16;      // R*2^26/ln2
    wire        [15:0] u_sh   = u_prod >>> 26;
    wire        [7:0]  idx_c  = (u_sh > 16'd255) ? 8'd255 : u_sh[7:0];
    wire        [15:0] frac_c = u_prod[25:10];
    wire signed [41:0] v_prod = bn_r * INV_ANG;         // B_N*1024*2^26/(2π*2^18)
    wire        [15:0] v_sh   = v_prod >>> 26;
    wire        [9:0]  j_c    = (v_sh > 16'd1023) ? 10'd1023 : v_sh[9:0];
    wire        [15:0] f_c    = v_prod[25:10];
    wire signed [5:0]  sh_c   = -(k_r + 8'sd1);

    // ---------------- ROM：exp 成对单地址读；角度分两拍读 LUT[j] / LUT[j+1] ----------------
    wire [8:0]  rom_exp_addr = (state == S_ROMA) ? {1'b0, idx_r} : 9'd0;
    wire [9:0]  rom_ang_addr = (state == S_ROMA) ? j_r
                             : ((state == S_ROMB) ? ((j_r + 10'd1) & 10'h3FF) : j_r);
    minphase_rom_1024 u_rom (
        .clk(clk), .exp_addr(rom_exp_addr), .exp_lo(exp_lo), .exp_hi(exp_hi),
        .ang_addr(rom_ang_addr), .cos_q(cos_q), .sin_q(sin_q)
    );

    // ---------------- S_ROMB：exp 差值（LO/HI 已由 ROM 寄存输出） ----------------
    wire signed [19:0] exp_lo_s  = $signed({2'b00, exp_lo});
    wire signed [19:0] exp_hi_s  = $signed({2'b00, exp_hi});
    wire signed [20:0] exp_dif_c = exp_hi_s - exp_lo_s;

    // ---------------- S_EXPM：exp 乘 frac；cos/sin 差值 ----------------
    wire signed [18:0] cos_l19 = {cos_l_r[17], cos_l_r};
    wire signed [18:0] sin_l19 = {sin_l_r[17], sin_l_r};
    wire signed [18:0] cos_h19 = {cos_q[17], cos_q};
    wire signed [18:0] sin_h19 = {sin_q[17], sin_q};
    wire signed [18:0] cos_dif_c = cos_h19 - cos_l19;   // 19 位差值，不溢出
    wire signed [18:0] sin_dif_c = sin_h19 - sin_l19;
    wire signed [36:0] exp_prod_c = exp_dif_r * $signed({1'b0, frac_r});

    // ---------------- S_EQ16：e_q16 = LO + (prod>>>16)；cos/sin 乘 F ----------------
    wire signed [20:0] exp_sh  = $signed(exp_prod_r[36:16]);
    wire signed [23:0] e_q16_c = $signed({{6{1'b0}}, exp_lo_d})
                               + $signed({{3{exp_sh[20]}}, exp_sh});
    wire signed [34:0] cos_prod_c = cos_dif_r * $signed({1'b0, f_r});
    wire signed [34:0] sin_prod_c = sin_dif_r * $signed({1'b0, f_r});

    // ---------------- S_EQ17：e_q17 移位；cos/sin = LUT[j] + 插值 ----------------
    wire signed [23:0] e_q17_c = sh_r[5] ? (e_q16_r <<< (-sh_r))
                                         : (e_q16_r >>> sh_r);
    wire signed [18:0] cos_sh  = $signed(cos_prod_r[34:16]);
    wire signed [18:0] sin_sh  = $signed(sin_prod_r[34:16]);
    wire signed [18:0] cos_sum = {cos_l_d[17], cos_l_d} + cos_sh;
    wire signed [18:0] sin_sum = {sin_l_d[17], sin_l_d} + sin_sh;

    // ---------------- S_MUL：Q2.17 复数乘 ----------------
    wire signed [38:0] yre_full_c = e_q17_r * cos_r;    // 21x18 → 精确 39 位
    wire signed [38:0] yim_full_c = e_q17_r * sin_r;

    // ---------------- S_RND：模型同款舍入 + 饱和 ----------------
    wire signed [38:0] yre_rnd = yre_full_r + $signed({{18{1'b0}}, RND_Q17[20:0]});
    wire signed [38:0] yim_rnd = yim_full_r + $signed({{18{1'b0}}, RND_Q17[20:0]});
    wire signed [38:0] yre_sh  = yre_rnd >>> 17;
    wire signed [38:0] yim_sh  = yim_rnd >>> 17;
    wire signed [21:0] yre_c   = yre_sh[21:0];
    wire signed [21:0] yim_c   = yim_sh[21:0];

    // ---------------- 输出饱和（20 位有符号） ----------------
    function signed [19:0] sat20;
        input signed [21:0] v;
        begin
            if (v > 22'sd524287) sat20 = 20'sd524287;
            else if (v < -22'sd524288) sat20 = -20'sd524288;
            else sat20 = v[19:0];
        end
    endfunction

    assign s_axis_tready = rst_n && (state == S_IDLE);
    assign busy          = (state != S_IDLE);
    assign m_axis_tvalid = m_valid_r;
    assign m_axis_tdata  = {{24{1'b0}}, y_im_r, y_re_r};
    assign m_axis_tlast  = m_valid_r && m_last_r;

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= S_IDLE; bin_cnt <= 10'd0; last_r <= 1'b0;
            m_valid_r <= 1'b0; m_last_r <= 1'b0; done <= 1'b0;
            a_r <= 24'sd0; b_r <= 24'sd0;
            k0_r <= 8'sd0; r0_r <= 25'sd0; k_r <= 8'sd0; r_r <= 24'sd0; bn_r <= 25'sd0;
            idx_r <= 8'd0; frac_r <= 16'd0; j_r <= 10'd0; f_r <= 16'd0; sh_r <= 6'sd0;
            exp_dif_r <= 21'sd0; exp_lo_d <= 18'd0;
            cos_l_r <= 18'sd0; sin_l_r <= 18'sd0; cos_l_d <= 18'sd0; sin_l_d <= 18'sd0;
            exp_prod_r <= 37'sd0; cos_dif_r <= 19'sd0; sin_dif_r <= 19'sd0;
            e_q16_r <= 24'sd0; cos_prod_r <= 35'sd0; sin_prod_r <= 35'sd0;
            e_q17_r <= 21'sd0; cos_r <= 18'sd0; sin_r <= 18'sd0;
            yre_full_r <= 39'sd0; yim_full_r <= 39'sd0;
            y_re_r <= 20'sd0; y_im_r <= 20'sd0;
        end else begin
            done <= 1'b0;
            case (state)
                S_IDLE: if (s_axis_tvalid) begin
                    a_r <= s_axis_tdata[23:0];
                    b_r <= s_axis_tdata[47:24];
                    last_r <= s_axis_tlast;
                    state <= S_K;
                end
                S_K: begin
                    k0_r <= k0_c;
                    state <= S_R0;
                end
                S_R0: begin
                    r0_r <= r0_c;
                    state <= S_RC;
                end
                S_RC: begin
                    k_r  <= k2_c;
                    r_r  <= r2_c[23:0];
                    bn_r <= bn_c;
                    state <= S_ADDR;
                end
                S_ADDR: begin
                    idx_r  <= idx_c;
                    frac_r <= frac_c;
                    j_r    <= j_c;
                    f_r    <= f_c;
                    sh_r   <= sh_c;
                    state <= S_ROMA;
                end
                S_ROMA: begin
                    // ROM 地址本拍有效：exp 成对表 + LUT[j] 在下一拍输出
                    state <= S_ROMB;
                end
                S_ROMB: begin
                    // exp 对 {e_{idx+1},e_idx} 与 LUT[j] 已就绪；角度地址切到 j+1
                    exp_dif_r <= exp_dif_c;
                    exp_lo_d  <= exp_lo;
                    cos_l_r   <= cos_q;
                    sin_l_r   <= sin_q;
                    state <= S_EXPM;
                end
                S_EXPM: begin
                    // LUT[j+1] 就绪：exp 乘 frac；cos/sin 求差值；LUT[j] 延迟一拍
                    exp_prod_r <= exp_prod_c;
                    cos_dif_r  <= cos_dif_c;
                    sin_dif_r  <= sin_dif_c;
                    cos_l_d    <= cos_l_r;
                    sin_l_d    <= sin_l_r;
                    state <= S_EQ16;
                end
                S_EQ16: begin
                    e_q16_r    <= e_q16_c;
                    cos_prod_r <= cos_prod_c;
                    sin_prod_r <= sin_prod_c;
                    state <= S_EQ17;
                end
                S_EQ17: begin
                    e_q17_r <= e_q17_c[20:0];
                    cos_r   <= cos_sum[17:0];
                    sin_r   <= sin_sum[17:0];
                    state <= S_MUL;
                end
                S_MUL: begin
                    yre_full_r <= yre_full_c;
                    yim_full_r <= yim_full_c;
                    state <= S_RND;
                end
                S_RND: begin
                    y_re_r <= sat20(yre_c);
                    y_im_r <= sat20(yim_c);
                    m_valid_r <= 1'b1;
                    m_last_r  <= (bin_cnt == 10'd512);
                    state <= S_OUT;
                end
                S_OUT: begin
                    if (m_axis_tready) begin
                        m_valid_r <= 1'b0;
                        if (bin_cnt == 10'd512) begin
                            bin_cnt <= 10'd0;
                            done <= 1'b1;
                            state <= S_IDLE;
                        end else begin
                            bin_cnt <= bin_cnt + 10'd1;
                            state <= S_IDLE;
                        end
                    end
                end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule

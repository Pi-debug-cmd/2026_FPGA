`timescale 1ns/1ps
// ============================================================================
// WORLD 最小相位加速器 · 复数 exp 单元（增量 2 步骤 1）
//
// 功能：对 513 个 bin 计算 y = exp(a) * (cos b, sin b)
//   输入 a = log_spectrum/1024（Q5.18，24 位有符号）
//        b = im/1024（Q5.18，24 位有符号；<0 时内部 +2π 归一到 [0,2π)）
//   输出 y_re/y_im Q2.17（20 位有符号，覆盖 |y|max≈1.115，不削顶）
//
// 与 Python 定点模型（cpu_breakdown/gen_exp_vectors.py）逐位一致：
//   K  = (A*94548) >>> 34                      # floor(a/ln2)
//   R  = A - K*181704（越界时 ±ln2 修正 K）
//   IDX= (R*94548) >>> 26 ; FRAC = (R*94548)[25:10]
//   E_Q16 = EXP[IDX] + ((EXP_HI-EXP[IDX])*FRAC >>> 16)
//   E_Q17 = SH>=0 ? E_Q16>>>SH : E_Q16<<(-SH), SH=-(K+1)
//   J  = (B_N*41722) >>> 26 ; F = (B_N*41722)[25:10]
//   COS/SIN = LUT[J] + ((LUT[(J+1)&1023]-LUT[J])*F >>> 16)
//   Y_RE = (E_Q17*COS + 2^17/2) >>> 17（其余同理），饱和到 20 位
//
// AXI-Stream：513 拍进 / 513 拍出，tdata 打包见端口注释；valid/ready 背压。
// 串行每 bin 约 7 拍：@100 MHz、400 次/s（513 bin）约 1.4% 占空比。
// 资源（OOC 综合见报告）：ROM 1×RAMB36（cos/sin 1024x36）+ 1×RAMB18（exp 256x18）、
// 约 6 个 DSP、约 1.5-2k LUT。
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
    localparam [2:0] S_IDLE = 3'd0, S_C1 = 3'd1, S_C2 = 3'd2,
                     S_ROM = 3'd3, S_ROM2 = 3'd4, S_MUL = 3'd5, S_OUT = 3'd6;

    reg [2:0]  state;
    reg [23:0] a_r, b_r;
    reg [9:0]  bin_cnt;          // 0..512
    reg        last_r;
    reg        m_valid_r, m_last_r;
    reg signed [19:0] y_re_r, y_im_r;

    // C1/C2 中间寄存器
    reg signed [7:0]  k_r;
    reg signed [23:0] r_r;
    reg [7:0]  idx_r;
    reg [15:0] frac_r;
    reg [9:0]  j_r;
    reg [15:0] f_r;
    reg signed [5:0] sh_r;

    // ROM 输出
    wire [17:0] exp_lo, exp_hi;
    wire signed [17:0] cos_q, sin_q;
    reg  [17:0] exp_lo_r, exp_hi_r;
    reg  signed [17:0] cos_r, sin_r;
    reg  signed [17:0] cos_l_r, sin_l_r, cos_i_r, sin_i_r;
    reg  signed [19:0] e_q17_r;

    // ---------------- C2 组合：指数/角度插值地址 ----------------
    wire signed [24:0] bn = b_r[23] ? ({b_r[23], b_r} + 25'sd1647099)
                                    : {b_r[23], b_r};
    wire signed [41:0] u_prod = r_r * 24'sd94548;
    wire [7:0] idx_c = (u_prod >>> 26) > 42'sd255 ? 8'd255 : (u_prod >>> 26);
    wire [15:0] frac_c = u_prod[25:10];
    wire signed [41:0] v_prod = bn * 25'sd41722;
    wire [9:0] j_c = (v_prod >>> 26) > 42'sd1023 ? 10'd1023 : (v_prod >>> 26);
    wire [15:0] f_c = v_prod[25:10];

    // ---------------- C1 组合：floor(a/ln2) 与 R ----------------
    wire signed [41:0] k_prod = a_r * 24'sd94548;
    wire signed [7:0]  k0 = k_prod >>> 34;
    wire signed [24:0] r0 = {a_r[23], a_r} - (k0 * 25'sd181704);
    wire signed [24:0] r1 = (r0 < 0) ? (r0 + 25'sd181704) : r0;
    wire signed [7:0]  k1 = (r0 < 0) ? (k0 - 8'sd1) : k0;
    wire signed [24:0] r2 = (r1 >= 25'sd181704) ? (r1 - 25'sd181704) : r1;
    wire signed [7:0]  k2 = (r1 >= 25'sd181704) ? (k1 + 8'sd1) : k1;

    // ---------------- ROM：两次读实现 cos/sin 线性插值 ----------------
    wire [8:0]  rom_exp_addr = (state == S_C2) ? {1'b0, idx_c} : {1'b0, idx_r};
    wire [9:0]  rom_ang_addr = (state == S_C2) ? j_c
                             : ((state == S_ROM) ? ((j_r + 10'd1) & 10'h3FF) : j_r);
    minphase_rom_1024 u_rom (
        .clk(clk), .exp_addr(rom_exp_addr), .exp_lo(exp_lo), .exp_hi(exp_hi),
        .ang_addr(rom_ang_addr), .cos_q(cos_q), .sin_q(sin_q)
    );

    // ---------------- 输出 ----------------
    function signed [19:0] sat20;
        input signed [21:0] v;
        begin
            if (v > 22'sd524287) sat20 = 20'sd524287;
            else if (v < -22'sd524288) sat20 = -20'sd524288;
            else sat20 = v[19:0];
        end
    endfunction

    wire signed [19:0] exp_lo_s = {2'b00, exp_lo_r};
    wire signed [19:0] exp_hi_s = {2'b00, exp_hi_r};
    wire signed [19:0] exp_dif  = exp_hi_s - exp_lo_s;
    wire signed [35:0] exp_prod = exp_dif * $signed({1'b0, frac_r});
    wire signed [19:0] e_q16 = exp_lo_s + (exp_prod >>> 16);
    wire signed [19:0] e_q17 = sh_r[5] ? (e_q16 <<< (-sh_r)) : (e_q16 >>> sh_r);

    wire signed [39:0] yre_full = e_q17_r * cos_r;
    wire signed [39:0] yim_full = e_q17_r * sin_r;
    wire signed [21:0] yre_c = (yre_full + 40'sd65536) >>> 17;
    wire signed [21:0] yim_c = (yim_full + 40'sd65536) >>> 17;

    assign s_axis_tready = rst_n && (state == S_IDLE);
    assign busy          = (state != S_IDLE);
    assign m_axis_tvalid = m_valid_r;
    assign m_axis_tdata  = {{24{1'b0}}, y_im_r, y_re_r};
    assign m_axis_tlast  = m_valid_r && m_last_r;

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= S_IDLE; bin_cnt <= 10'd0; last_r <= 1'b0;
            m_valid_r <= 1'b0; m_last_r <= 1'b0; done <= 1'b0;
            a_r <= 24'sd0; b_r <= 24'sd0; k_r <= 8'sd0; r_r <= 24'sd0;
            idx_r <= 8'd0; frac_r <= 16'd0; j_r <= 10'd0; f_r <= 16'd0;
            sh_r <= 6'sd0; exp_lo_r <= 18'd0; exp_hi_r <= 18'd0;
            cos_r <= 18'sd0; sin_r <= 18'sd0; e_q17_r <= 20'sd0;
            y_re_r <= 20'sd0; y_im_r <= 20'sd0;
        end else begin
            done <= 1'b0;
            case (state)
                S_IDLE: if (s_axis_tvalid) begin
                    a_r <= s_axis_tdata[23:0];
                    b_r <= s_axis_tdata[47:24];
                    last_r <= s_axis_tlast;
                    state <= S_C1;
                end
                S_C1: begin
                    k_r <= k2;
                    r_r <= r2[23:0];
                    state <= S_C2;
                end
                S_C2: begin
                    // ROM 地址在本拍有效，下一拍数据到达
                    idx_r <= idx_c; frac_r <= frac_c;
                    j_r <= j_c; f_r <= f_c;
                    sh_r <= -(k_r + 8'sd1);
                    state <= S_ROM;
                end
                S_ROM: begin
                    // 本拍：cos/sin LUT[j]、exp LUT[idx]；同时把角度地址切到 j+1
                    exp_lo_r <= exp_lo; exp_hi_r <= exp_hi;
                    cos_l_r <= cos_q; sin_l_r <= sin_q;
                    state <= S_ROM2;
                end
                S_ROM2: begin
                    // 本拍：cos/sin LUT[j+1]；与模型相同的插值 + 指数定标
                    cos_r <= cos_l_r + (((cos_q - cos_l_r) * f_r) >>> 16);
                    sin_r <= sin_l_r + (((sin_q - sin_l_r) * f_r) >>> 16);
                    e_q17_r <= e_q17;
                    state <= S_MUL;
                end
                S_MUL: begin
                    y_re_r <= sat20(yre_c);
                    y_im_r <= sat20(yim_c);
                    m_valid_r <= 1'b1;
                    m_last_r <= (bin_cnt == 10'd512);
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

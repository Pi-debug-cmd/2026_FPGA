`timescale 1ns/1ps
// ---------------------------------------------------------------------------
// axis_stft_gain - STFT / per-bin real gain / ISTFT frame engine (pure RTL).
//
// The two 1024-point FFTs are instantiated in the block design as xfft 9.1 IP
// cells and wired to this module, so the module itself contains no IP: that is
// what lets it be synthesised both standalone and as a BD module reference.
//
// Slave frame  : [ N x 16-bit windowed samples ]  [ NBIN x 24-bit gains Q4.19 ]
// Master frame : [ N x 32-bit samples ]  value = round(z * 32768 * 256)
//
// Fixed point plan (both FFTs UNSCALED, so every factor is explicit here):
//   a[n] = x[n]                                (int16 units, 24-bit)
//   A[k] = sum a[n] e^-i                       (unscaled FFT, |A| <= 2^25)
//   Y[k] = round(A[k] * g_q / 2^13)            (g_q = g*2^19, 6 fractional bits)
//   y[n] = sum Y[k] e^+i = 2^16 * z[n]         (unscaled IFFT)
//   out  = round(y / 2^8) = z * 2^8
// Worst case |A*g| ~ 2^24 for full-scale speech -> |Y| ~ 2^30 < 2^31 (saturates).
// ---------------------------------------------------------------------------
module axis_stft_gain #(
    parameter integer N     = 1024,
    parameter integer NBIN  = 513
)(
    input  wire        aclk,
    input  wire        aresetn,

    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 s_axis TDATA" *)
    input  wire [31:0] s_axis_tdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 s_axis TVALID" *)
    input  wire        s_axis_tvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 s_axis TREADY" *)
    output wire        s_axis_tready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 s_axis TLAST" *)
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME s_axis,TDATA_NUM_BYTES 4,TUSER_WIDTH 0,HAS_TKEEP 0,HAS_TSTRB 0" *)
    input  wire        s_axis_tlast,

    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TDATA" *)
    output reg  [31:0] m_axis_tdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TVALID" *)
    output reg         m_axis_tvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TREADY" *)
    input  wire        m_axis_tready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TLAST" *)
    output reg         m_axis_tlast,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TKEEP" *)
    output wire [3:0]  m_axis_tkeep,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TSTRB" *)
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME m_axis,TDATA_NUM_BYTES 4,TUSER_WIDTH 0,HAS_TKEEP 1,HAS_TSTRB 1" *)
    output wire [3:0]  m_axis_tstrb,

    // ---- forward xfft (BD cell) ----
    output reg  [7:0]  fwd_cfg_tdata,
    output reg         fwd_cfg_tvalid,
    input  wire        fwd_cfg_tready,
    output wire [47:0] fwd_s_tdata,
    output wire        fwd_s_tvalid,
    input  wire        fwd_s_tready,
    output wire        fwd_s_tlast,
    input  wire [79:0] fwd_m_tdata,
    input  wire        fwd_m_tvalid,
    output wire        fwd_m_tready,
    input  wire        fwd_m_tlast,
    input  wire        fwd_unexp,
    input  wire        fwd_miss,

    // ---- inverse xfft (BD cell) ----
    output reg  [7:0]  inv_cfg_tdata,
    output reg         inv_cfg_tvalid,
    input  wire        inv_cfg_tready,
    output wire [63:0] inv_s_tdata,
    output wire        inv_s_tvalid,
    input  wire        inv_s_tready,
    output wire        inv_s_tlast,
    input  wire [95:0] inv_m_tdata,
    input  wire        inv_m_tvalid,
    output wire        inv_m_tready,
    input  wire        inv_m_tlast,
    input  wire        inv_unexp,
    input  wire        inv_miss,

    output reg  [31:0] status
);

    localparam [3:0] S_IDLE = 4'd0, S_SAMP = 4'd1, S_GAIN = 4'd2, S_CFG = 4'd3,
                     S_FEED = 4'd4, S_CAP  = 4'd5, S_MULT = 4'd6, S_IFEED = 4'd7,
                     S_OUT  = 4'd8;

    reg [3:0]  state;
    reg [10:0] cnt;
    reg [9:0]  gcnt;
    reg [10:0] fcnt;
    reg [10:0] micnt;
    reg [31:0] frame_cnt;
    reg        st_busy, st_miss, st_unexp, st_sat;

    // ---- sample RAM 1024 x 24 -------------------------------------------
    reg [23:0] samp_ram [0:N-1];
    reg        samp_we;
    reg [9:0]  samp_wa;
    reg [23:0] samp_wd;
    reg [9:0]  samp_ra;
    reg [23:0] samp_rd;
    always @(posedge aclk) begin
        if (samp_we) samp_ram[samp_wa] <= samp_wd;
        samp_rd <= samp_ram[samp_ra];
    end

    // ---- gain RAM 513 x 24 ----------------------------------------------
    reg [23:0] gain_ram [0:NBIN-1];
    reg        gain_we;
    reg [9:0]  gain_wa;
    reg [23:0] gain_wd;
    reg [9:0]  gain_ra;
    reg [23:0] gain_rd;
    always @(posedge aclk) begin
        if (gain_we) gain_ram[gain_wa] <= gain_wd;
        gain_rd <= gain_ram[gain_ra];
    end

    // ---- spectrum RAM A (forward FFT output, 1024 x 80) ------------------
    // Write port driven directly from the FSM (combinational index).  Routing the
    // write address through a register as well as the data leaves the two one
    // cycle out of phase and rotates the whole frame by one bin.
    reg [79:0] spec_a [0:N-1];
    reg [9:0]  sa_wa;
    reg [9:0]  sa_ra;
    reg [79:0] sa_rd;
    always @(posedge aclk) begin
        if (state == S_CAP && fwd_m_tvalid) spec_a[sa_wa] <= fwd_m_tdata;
        sa_rd <= spec_a[sa_ra];
    end

    // ---- spectrum RAM B (after gain, 1024 x 64: 24-bit re + 24-bit im) ---
    reg [63:0] spec_b [0:N-1];
    reg [9:0]  sb_ra;
    reg [63:0] sb_rd;
    always @(posedge aclk) begin
        if (v3) spec_b[micnt - 11'd4] <= {yq(p_im), yq(p_re)};
        sb_rd <= spec_b[sb_ra];
    end

    // AXIS master byte qualifiers: the whole 32-bit word is always valid data
    assign m_axis_tkeep = 4'hf;
    assign m_axis_tstrb = 4'hf;

    // m_tready are combinational: a registered tready is one cycle out of phase
    // with the capture condition, which drops or duplicates the first word.
    assign fwd_m_tready = (state == S_CAP);
    assign inv_m_tready = (state == S_OUT) && (!m_axis_tvalid || m_axis_tready);

    // =====================================================================
    // slave input
    // =====================================================================
    assign s_axis_tready = aresetn &&
                           ((state == S_IDLE) || (state == S_SAMP) || (state == S_GAIN));

    always @(*) begin
        samp_we = 1'b0;
        samp_wa = cnt[9:0];
        samp_wd = 24'd0;
        gain_we = 1'b0;
        gain_wa = gcnt;
        gain_wd = 24'd0;
        if (s_axis_tvalid && s_axis_tready) begin
            if (state == S_IDLE || state == S_SAMP) begin
                samp_we = 1'b1;
                samp_wd = {{8{s_axis_tdata[15]}}, s_axis_tdata[15:0]};
            end else begin
                gain_we = 1'b1;
                gain_wd = s_axis_tdata[23:0];
            end
        end
    end

    // feed pipelines
    reg        fwd_s_tvalid_r;
    reg [47:0] fwd_s_tdata_r;
    reg        fwd_s_tlast_r;
    assign fwd_s_tvalid = fwd_s_tvalid_r;
    assign fwd_s_tdata  = fwd_s_tdata_r;
    assign fwd_s_tlast  = fwd_s_tlast_r;

    reg        inv_s_tvalid_r;
    reg [63:0] inv_s_tdata_r;
    reg        inv_s_tlast_r;
    assign inv_s_tvalid = inv_s_tvalid_r;
    assign inv_s_tdata  = inv_s_tdata_r;
    assign inv_s_tlast  = inv_s_tlast_r;

    // =====================================================================
    // gain multiply, 3 stages, one bin per cycle
    // =====================================================================
    wire signed [39:0] sa_re = sa_rd[39:0];
    wire signed [39:0] sa_im = sa_rd[79:40];

    reg signed [39:0] a_re_q, a_im_q;
    reg signed [23:0] g_q;
    reg signed [63:0] p_re, p_im;
    reg               v1, v2, v3;

    function signed [31:0] yq;
        input signed [63:0] p;
        reg signed [63:0] t;
        begin
            t = (p + 64'sd4096) >>> 13;         // +2^12, /2^13 (19 - 6)
            if (t > 64'sd2147483647)        yq = 32'sh7fffffff;
            else if (t < -64'sd2147483648)  yq = -32'sd2147483648;
            else                            yq = t[31:0];
        end
    endfunction

    // =====================================================================
    // output pack: 48-bit real -> 32-bit word
    // =====================================================================
    wire signed [47:0] inv_re = inv_m_tdata[47:0];
    // {a,b} is UNSIGNED in Verilog, so the concatenation must be cast back to
    // signed before the add/shift - otherwise negative samples saturate to +MAX.
    wire signed [51:0] inv_ext = $signed({{4{inv_re[47]}}, inv_re});
    wire signed [51:0] inv_rd  = (inv_ext + 52'sd128) >>> 8;
    reg  [31:0] out_word;
    always @(*) begin
        if (inv_rd > 52'sd2147483647)       out_word = 32'h7fffffff;
        else if (inv_rd < -52'sd2147483648) out_word = 32'h80000000;
        else                                out_word = inv_rd[31:0];
    end

    // =====================================================================
    // FSM
    // =====================================================================
    always @(posedge aclk) begin
        if (!aresetn) begin
            state  <= S_IDLE;
            cnt    <= 11'd0;  gcnt  <= 10'd0;  fcnt <= 11'd0;  micnt <= 11'd0;
            frame_cnt <= 32'd0;
            st_busy <= 1'b0; st_miss <= 1'b0; st_unexp <= 1'b0; st_sat <= 1'b0;
            samp_ra <= 10'd0; gain_ra <= 10'd0;
            sa_wa <= 10'd0; sa_ra <= 10'd0;
            sb_ra <= 10'd0;
            fwd_s_tvalid_r <= 1'b0; fwd_s_tdata_r <= 48'd0; fwd_s_tlast_r <= 1'b0;
            fwd_cfg_tvalid <= 1'b0; fwd_cfg_tdata <= 8'h01;
            inv_cfg_tvalid <= 1'b0; inv_cfg_tdata <= 8'h00;
            inv_s_tvalid_r <= 1'b0; inv_s_tdata_r <= 64'd0; inv_s_tlast_r <= 1'b0;
            m_axis_tvalid <= 1'b0; m_axis_tdata <= 32'd0; m_axis_tlast <= 1'b0;
            v1 <= 1'b0; v2 <= 1'b0; v3 <= 1'b0;
            a_re_q <= 40'd0; a_im_q <= 40'd0; g_q <= 24'd0;
            p_re <= 64'd0; p_im <= 64'd0;
            status <= 32'd0;
        end else begin
            if (fwd_miss || inv_miss)   st_miss  <= 1'b1;
            if (fwd_unexp || inv_unexp) st_unexp <= 1'b1;
            if (m_axis_tvalid && m_axis_tready) m_axis_tvalid <= 1'b0;
            if (fwd_cfg_tvalid && fwd_cfg_tready) fwd_cfg_tvalid <= 1'b0;
            if (inv_cfg_tvalid && inv_cfg_tready) inv_cfg_tvalid <= 1'b0;

            case (state)
            // -------------------------------------------------------------
            S_IDLE: begin
                cnt     <= 11'd0;
                st_busy <= 1'b0;
                if (s_axis_tvalid) begin
                    cnt     <= 11'd1;   // sample 0 is written to address 0 this cycle
                    state   <= S_SAMP;
                    st_busy <= 1'b1;
                end
            end
            // -------------------------------------------------------------
            S_SAMP: begin
                if (s_axis_tvalid) begin
                    if (cnt == N-1) begin
                        cnt   <= 11'd0;
                        gcnt  <= 10'd0;
                        state <= S_GAIN;
                    end else cnt <= cnt + 11'd1;
                end
            end
            // -------------------------------------------------------------
            S_GAIN: begin
                if (s_axis_tvalid) begin
                    if (gcnt == NBIN-1) begin
                        gcnt           <= 10'd0;
                        state          <= S_CFG;
                        fwd_cfg_tdata  <= 8'h01;   // FWD_INV = 1
                        inv_cfg_tdata  <= 8'h00;   // FWD_INV = 0
                        fwd_cfg_tvalid <= 1'b1;
                        inv_cfg_tvalid <= 1'b1;
                    end else gcnt <= gcnt + 10'd1;
                end
            end
            // -------------------------------------------------------------
            S_CFG: begin
                if (!fwd_cfg_tvalid && !inv_cfg_tvalid) begin
                    fcnt    <= 11'd0;
                    samp_ra <= 10'd0;   // first BRAM read happens in S_FEED
                    state   <= S_FEED;
                end
            end
            // -------------------------------------------------------------
            // one word every other cycle: present, wait for tready, clear, next.
            S_FEED: begin
                if (!fwd_s_tvalid_r) begin
                    fwd_s_tdata_r  <= {24'd0, samp_rd};
                    fwd_s_tvalid_r <= 1'b1;
                    fwd_s_tlast_r  <= (fcnt == N-1);
                    samp_ra        <= fcnt[9:0] + 10'd1;
                end else if (fwd_s_tready) begin
                    fwd_s_tvalid_r <= 1'b0;
                    if (fcnt == N-1) begin
                        fcnt  <= 11'd0;
                        state <= S_CAP;
                    end else fcnt <= fcnt + 11'd1;
                end
            end
            // -------------------------------------------------------------
            S_CAP: begin
                if (fwd_m_tvalid) begin
                    sa_wa <= sa_wa + 10'd1;
                    if (sa_wa == N-1) begin
                        sa_wa  <= 10'd0;
                        state  <= S_MULT;
                        micnt  <= 11'd0;
                        v1 <= 1'b0; v2 <= 1'b0; v3 <= 1'b0;
                    end
                end
            end
            // -------------------------------------------------------------
            S_MULT: begin
                v1 <= (micnt < N);
                if (micnt < N) begin
                    sa_ra   <= micnt[9:0];
                    gain_ra <= (micnt < NBIN) ? micnt[9:0]
                                              : (11'd1024 - {1'b0, micnt[9:0]});
                end
                v2 <= v1;
                if (v1) begin
                    a_re_q <= sa_re;
                    a_im_q <= sa_im;
                    g_q    <= gain_rd;
                end
                v3 <= v2;
                if (v2) begin
                    p_re <= a_re_q * g_q;
                    p_im <= a_im_q * g_q;
                end
                if (micnt == N + 11'd4) begin
                    state <= S_IFEED;
                    fcnt  <= 11'd0;
                    sb_ra <= 10'd0;
                end else micnt <= micnt + 11'd1;
            end
            // -------------------------------------------------------------
            S_IFEED: begin
                if (!inv_s_tvalid_r) begin
                    inv_s_tdata_r  <= sb_rd;
                    inv_s_tvalid_r <= 1'b1;
                    inv_s_tlast_r  <= (fcnt == N-1);
                    sb_ra          <= fcnt[9:0] + 10'd1;
                end else if (inv_s_tready) begin
                    inv_s_tvalid_r <= 1'b0;
                    if (fcnt == N-1) begin
                        fcnt  <= 11'd0;
                        state <= S_OUT;
                    end else fcnt <= fcnt + 11'd1;
                end
            end
            // -------------------------------------------------------------
            S_OUT: begin
                if (inv_m_tvalid && inv_m_tready) begin
                    m_axis_tdata  <= out_word;
                    m_axis_tvalid <= 1'b1;
                    m_axis_tlast  <= inv_m_tlast;
                    if (inv_m_tlast) begin
                        state     <= S_IDLE;
                        frame_cnt <= frame_cnt + 32'd1;
                    end
                end
            end
            default: state <= S_IDLE;
            endcase

            status <= {frame_cnt[15:0], 12'd0, st_busy, st_sat, st_miss, st_unexp};
        end
    end

endmodule





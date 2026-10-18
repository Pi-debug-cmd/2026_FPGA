`timescale 1ns/1ps
// ============================================================================
// WORLD 合成卸载（增量 1）：1024 点 IFFT 核 testbench
//
// 自动比对 gen_ifft_vectors.py 生成的黄金向量：
//   - 每拍输入 {imag_q15, real_q15}（513 拍），随机 valid 空拍；
//   - 输出 1024 拍 Q1.17 实样本，随机 m_axis_tready 背压；
//   - 逐样本比对，统计最大绝对误差（Q1.17 LSB 与浮点幅度两种表示）；
//   - 判定：最大绝对误差 <= 1e-3（= 131 LSB，Q1.17），且相对误差 <= 1%
//           （相对误差用于 DC/Nyquist 这类幅度远小于 1e-3 的结构性用例）；
//   - 检查 TLAST、背压下输出稳定、无多余输出、收满 1024 点、done 脉冲。
// 同时把 RTL 输出写 case*_rtl.hex，便于和 Python 定点模型逐位核对。
// ============================================================================
module tb_ifft1024_stream;
    localparam integer NBINS = 513;
    localparam integer NFFT  = 1024;
    localparam integer NCASE = 6;
    localparam integer TOL_LSB = 131;          // 1e-3 * 2^17 = 131.072
    localparam real    TOL_ABS = 1.0e-3;
    localparam real    TOL_REL = 1.0e-2;

    reg clk = 0;
    always #5 clk = !clk;

    reg rst_n = 0;
    reg         s_axis_tvalid = 0;
    reg  [31:0] s_axis_tdata = 0;
    reg         s_axis_tlast = 0;
    wire        s_axis_tready;
    wire        m_axis_tvalid;
    reg         m_axis_tready = 0;
    wire [31:0] m_axis_tdata;
    wire        m_axis_tlast;
    wire        busy;
    wire        done;

    ifft1024_stream dut (
        .clk(clk), .rst_n(rst_n),
        .s_axis_tvalid(s_axis_tvalid), .s_axis_tready(s_axis_tready),
        .s_axis_tdata(s_axis_tdata),   .s_axis_tlast(s_axis_tlast),
        .m_axis_tvalid(m_axis_tvalid), .m_axis_tready(m_axis_tready),
        .m_axis_tdata(m_axis_tdata),   .m_axis_tlast(m_axis_tlast),
        .busy(busy), .done(done)
    );

    // 激励与黄金向量
    reg [31:0] stimulus [0:NBINS-1];
    reg [31:0] golden   [0:NFFT-1];

    string case_names [0:NCASE-1];
    initial begin
        case_names[0] = "impulse_full_band";
        case_names[1] = "multi_tone";
        case_names[2] = "world_like_minphase";
        case_names[3] = "random_broadband";
        case_names[4] = "nyquist_alternating";
        case_names[5] = "dc_only";
    end

    // 随机数（xorshift32），用于输入空拍与输出背压
    reg [31:0] rng = 32'h20261018;
    always @(posedge clk) begin
        rng <= {rng[30:0], rng[31] ^ rng[21] ^ rng[1] ^ rng[0]};
    end

    // 统计量
    integer case_idx;
    integer sent, received;
    integer max_err_lsb;
    integer peak_lsb;
    integer stalls_in, stalls_out;
    integer cycles;
    integer frame_start_cycle;
    integer frame_cycles;
    integer out_fd;
    real    max_err_float;
    real    rel_err;
    integer total_fail;
    reg running;
    reg first_case;
    reg [31:0] held_data;
    reg        held_last;
    reg        held_valid;

    // 周期计数
    always @(posedge clk) begin
        if (!rst_n) cycles <= 0;
        else cycles <= cycles + 1;
    end

    // ------------------------------------------------------------------
    // 输入源：513 拍，随机空拍；valid 一旦拉高保持到 ready
    // ------------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            s_axis_tvalid <= 1'b0;
            s_axis_tdata  <= 32'd0;
            s_axis_tlast  <= 1'b0;
            sent          <= 0;
        end else if (running) begin
            if (s_axis_tvalid && s_axis_tready) begin
                // 成功握手一拍
                sent <= sent + 1;
                if (sent + 1 < NBINS) begin
                    s_axis_tdata  <= stimulus[sent+1];
                    s_axis_tlast  <= ((sent + 1) == NBINS - 1);
                    s_axis_tvalid <= (rng[10:8] != 3'b000);  // 约 1/8 空拍
                end else begin
                    s_axis_tvalid <= 1'b0;
                    s_axis_tlast  <= 1'b0;
                end
            end else if (!s_axis_tvalid && (sent < NBINS)) begin
                s_axis_tdata  <= stimulus[sent];
                s_axis_tlast  <= (sent == NBINS - 1);
                s_axis_tvalid <= (rng[12:11] != 2'b00);      // 启动新拍
            end
        end
    end

    // 输出背压：随机 m_axis_tready
    always @(posedge clk) begin
        if (!rst_n) m_axis_tready <= 1'b0;
        else if (running) m_axis_tready <= (rng[0] | rng[2] | rng[5]);  // 约 87% ready
        else m_axis_tready <= 1'b0;
    end

    // ------------------------------------------------------------------
    // 输出接收、逐样本比对、背压稳定性检查
    // ------------------------------------------------------------------
    always @(posedge clk) begin
        if (rst_n && running) begin
            // 背压期间输出必须保持稳定
            if (held_valid) begin
                if (m_axis_tvalid &&
                    ((m_axis_tdata !== held_data) || (m_axis_tlast !== held_last)))
                    $fatal(1, "case %0d: output unstable under backpressure", case_idx);
            end
            if (m_axis_tvalid && !m_axis_tready) begin
                held_data  <= m_axis_tdata;
                held_last  <= m_axis_tlast;
                held_valid <= 1'b1;
                stalls_out <= stalls_out + 1;
            end else begin
                held_valid <= 1'b0;
            end

            if (m_axis_tvalid && m_axis_tready) begin
                if (received >= NFFT)
                    $fatal(1, "case %0d: extra output sample", case_idx);
                if (m_axis_tlast !== (received == NFFT - 1))
                    $fatal(1, "case %0d: TLAST mismatch at %0d", case_idx, received);
                if ($signed(m_axis_tdata) - $signed(golden[received]) > max_err_lsb)
                    max_err_lsb = $signed(m_axis_tdata) - $signed(golden[received]);
                if ($signed(golden[received]) - $signed(m_axis_tdata) > max_err_lsb)
                    max_err_lsb = $signed(golden[received]) - $signed(m_axis_tdata);
                if (out_fd != 0) $fwrite(out_fd, "%08x\n", m_axis_tdata);
                received = received + 1;
            end

            // 输入侧背压统计
            if (s_axis_tvalid && !s_axis_tready) stalls_in <= stalls_in + 1;
        end
    end

    // ------------------------------------------------------------------
    // 主流程
    // ------------------------------------------------------------------
    integer i;
    integer tmp;
    initial begin
        total_fail = 0;
        // 等 glbl 的 GSR（全局复位）释放：RAMB36E1 原语模型在 GSR=1 期间忽略写入，
        // 若在 0 ns 就开始写会丢掉第一帧的部分地址，所以先等 200 ns 再跑用例。
        #200;
        for (case_idx = 0; case_idx < NCASE; case_idx = case_idx + 1) begin
            // 读入本用例向量（文件在当前仿真目录）
            $readmemh($sformatf("case%0d_input.hex", case_idx), stimulus);
            $readmemh($sformatf("case%0d_expected.hex", case_idx), golden);

            // 复位并清空统计
            @(negedge clk);
            running = 0;
            rst_n   = 0;
            m_axis_tready = 0;
            s_axis_tvalid = 0;
            s_axis_tlast  = 0;
            sent = 0;
            received = 0;
            max_err_lsb = 0;
            stalls_in = 0;
            stalls_out = 0;
            held_valid = 0;
            // 黄金向量绝对值峰值（Q1.17 LSB），用于相对误差
            peak_lsb = 0;
            for (i = 0; i < NFFT; i = i + 1) begin
                tmp = $signed(golden[i]);
                if (tmp < 0) tmp = -tmp;
                if (tmp > peak_lsb) peak_lsb = tmp;
            end
            out_fd = $fopen($sformatf("case%0d_rtl.hex", case_idx), "w");

            repeat (3) @(negedge clk);
            rst_n = 1;
            @(negedge clk);
            running = 1;
            frame_start_cycle = cycles;

            wait (done);                 // 一帧结束
            frame_cycles = cycles - frame_start_cycle;
            @(negedge clk);
            running = 0;
            m_axis_tready = 0;
            repeat (2) @(negedge clk);
            if (out_fd != 0) $fclose(out_fd);

            max_err_float = max_err_lsb / 131072.0;
            rel_err = (peak_lsb == 0) ? 0.0 : (1.0 * max_err_lsb / peak_lsb);
            $display("CASE %0d %-20s received=%0d max_abs_err=%.3e (%0d LSB) rel_err=%.3e stalls_in=%0d stalls_out=%0d cycles=%0d",
                     case_idx, case_names[case_idx], received, max_err_float,
                     max_err_lsb, rel_err, stalls_in, stalls_out, frame_cycles);
            if (received != NFFT) begin
                $display("FAIL: case %0d received %0d samples, expected %0d",
                         case_idx, received, NFFT);
                total_fail = total_fail + 1;
            end else if (max_err_lsb > TOL_LSB) begin
                $display("FAIL: case %0d max abs err %0d LSB > %0d LSB (1e-3)",
                         case_idx, max_err_lsb, TOL_LSB);
                total_fail = total_fail + 1;
            end else if (rel_err > TOL_REL) begin
                $display("FAIL: case %0d rel err %.3e > %.3e", case_idx, rel_err, TOL_REL);
                total_fail = total_fail + 1;
            end else begin
                $display("PASS: case %0d %-20s", case_idx, case_names[case_idx]);
            end
        end

        // 帧间必须回到空闲、可再次接收
        @(negedge clk);
        rst_n = 1;
        repeat (2) @(negedge clk);
        if (!s_axis_tready) begin
            $display("FAIL: core not ready after frames");
            total_fail = total_fail + 1;
        end

        if (total_fail == 0)
            $display("PASS: %0d cases, 1024-point IFFT, max_abs_err<=%.1e (131 LSB, Q1.17), TLAST/backpressure/OLA-frame interface OK",
                     NCASE, TOL_ABS);
        else
            $display("FAIL: %0d case(s) failed", total_fail);
        $finish;
    end

    // 全局看门狗
    initial begin
        #20000000;
        $display("FAIL: global watchdog timeout");
        $finish;
    end
endmodule

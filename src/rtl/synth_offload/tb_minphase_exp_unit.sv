`timescale 1ns/1ps
// 复数 exp 单元 testbench：用 minphase_dump.bin 的 96 次真实调用做黄金数据，
// 逐 bin 与 Python 定点模型比对（要求 0 LSB，即 20 位字段完全相等）。
module tb_minphase_exp_unit;
    localparam integer NCALL = 96;
    localparam integer NBIN  = 513;
    localparam integer N     = NCALL * NBIN;

    reg clk = 0;
    always #5 clk = !clk;
    reg rst_n = 0;

    reg         s_axis_tvalid = 0;
    reg  [63:0] s_axis_tdata = 0;
    reg         s_axis_tlast = 0;
    wire        s_axis_tready;
    wire        m_axis_tvalid;
    reg         m_axis_tready = 1;
    wire [63:0] m_axis_tdata;
    wire        m_axis_tlast;
    wire        busy;
    wire        done;

    reg [63:0] inputs   [0:N-1];
    reg [63:0] expected [0:N-1];

    integer sent = 0, recvd = 0, errs = 0, lasterr = 0;
    integer maxdiff = 0, cur;
    integer c;
    reg [31:0] rng = 32'h1234abcd;
    always @(negedge clk) begin
        rng <= {rng[30:0], rng[31]^rng[21]^rng[1]^rng[0]};
        m_axis_tready <= (rng[3:0] < 6); // sustained randomized backpressure
    end

    minphase_exp_unit dut (
        .clk(clk), .rst_n(rst_n),
        .s_axis_tvalid(s_axis_tvalid), .s_axis_tready(s_axis_tready),
        .s_axis_tdata(s_axis_tdata), .s_axis_tlast(s_axis_tlast),
        .m_axis_tvalid(m_axis_tvalid), .m_axis_tready(m_axis_tready),
        .m_axis_tdata(m_axis_tdata), .m_axis_tlast(m_axis_tlast),
        .busy(busy), .done(done)
    );

    // 输入源
    always @(posedge clk) begin
        if (!rst_n) begin
            s_axis_tvalid <= 1'b0;
            s_axis_tdata  <= 64'd0;
            s_axis_tlast  <= 1'b0;
            sent <= 0;
        end else begin
            if (s_axis_tvalid && s_axis_tready) begin
                sent <= sent + 1;
                if (sent + 1 < N) begin
                    s_axis_tdata  <= inputs[sent + 1];
                    s_axis_tlast  <= (((sent + 1) % NBIN) == (NBIN - 1));
                    s_axis_tvalid <= 1'b1;
                end else begin
                    s_axis_tvalid <= 1'b0;
                    s_axis_tlast  <= 1'b0;
                end
            end else if (!s_axis_tvalid && sent < N) begin
                s_axis_tdata  <= inputs[sent];
                s_axis_tlast  <= ((sent % NBIN) == (NBIN - 1));
                s_axis_tvalid <= 1'b1;
            end
        end
    end

    // 输出比对（20 位字段必须完全相等）
    always @(posedge clk) begin
        if (rst_n && m_axis_tvalid && m_axis_tready) begin
            if (m_axis_tdata[19:0] !== expected[recvd][19:0] ||
                m_axis_tdata[39:20] !== expected[recvd][39:20]) begin
                errs <= errs + 1;
                if (lasterr < 8)
                    $display("MISMATCH bin=%0d got re=%0d im=%0d exp re=%0d im=%0d",
                             recvd, $signed(m_axis_tdata[19:0]),
                             $signed(m_axis_tdata[39:20]),
                             $signed(expected[recvd][19:0]),
                             $signed(expected[recvd][39:20]));
                lasterr <= lasterr + 1;
            end
            cur = $signed(m_axis_tdata[19:0]) - $signed(expected[recvd][19:0]);
            if (cur < 0) cur = -cur;
            if (cur > maxdiff) maxdiff <= cur;
            cur = $signed(m_axis_tdata[39:20]) - $signed(expected[recvd][39:20]);
            if (cur < 0) cur = -cur;
            if (cur > maxdiff) maxdiff <= cur;
            if (m_axis_tlast !== (((recvd % NBIN) == (NBIN - 1))))
                $fatal(1, "TLAST mismatch at bin %0d", recvd);
            recvd <= recvd + 1;
        end
    end

    initial begin
        $readmemh("exp_input.hex", inputs);
        $readmemh("exp_expected.hex", expected);
        // 后综合 funcsim 带 glbl GSR（约前 100 ns 全局复位寄存器）；行为级仿真无 GSR。
        // 统一先等 200 ns 再释放 rst_n，保证两种仿真激励对齐（与增量 1 的 TB 同一处理）。
        #200;
        repeat (3) @(negedge clk);
        rst_n = 1;
        wait (recvd == N);
        repeat (3) @(negedge clk);
        if (errs == 0 && maxdiff == 0 && recvd == N)
            $display("PASS: %0d calls / %0d bins, exp unit 20-bit fields bit-exact (0 LSB)",
                     NCALL, N);
        else
            $fatal(1,"FAIL: recvd=%0d errs=%0d maxdiff=%0d LSB", recvd, errs, maxdiff);
        $finish;
    end

    initial begin
        #50000000;
        $fatal(1,"FAIL: watchdog");
        $finish;
    end
endmodule

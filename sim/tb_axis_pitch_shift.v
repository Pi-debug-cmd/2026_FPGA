`timescale 1ns/1ps
module tb_axis_pitch_shift;
    localparam COUNT = 4096;
    reg clk = 0;
    always #5 clk = !clk;
    reg resetn = 0;
    reg [17:0] ratio_q16 = 65536;
    reg [31:0] input_data = 0;
    reg input_last = 0, input_valid = 0;
    wire input_ready;
    wire [31:0] output_data;
    wire [3:0] output_keep;
    wire output_last, output_valid;
    reg output_ready = 0;
    reg [31:0] inputs [0:COUNT-1];
    reg [31:0] expected [0:COUNT-1];
    reg [17:0] ratios [0:5];
    integer sent = 0, received = 0, cycles = 0, case_index;
    reg running = 0, source_stalled = 0, output_stalled = 0;
    reg [36:0] held_output = 0;
    reg [31:0] random_state = 32'h20261009;

    axis_pitch_shift dut (
        .aclk(clk), .aresetn(resetn), .ratio_q16(ratio_q16),
        .s_axis_tdata(input_data), .s_axis_tkeep(4'hf),
        .s_axis_tlast(input_last), .s_axis_tvalid(input_valid),
        .s_axis_tready(input_ready), .m_axis_tdata(output_data),
        .m_axis_tkeep(output_keep), .m_axis_tlast(output_last),
        .m_axis_tvalid(output_valid), .m_axis_tready(output_ready)
    );
    function sample_last;
        input integer index;
        begin sample_last = (index % 37 == 36) || (index == COUNT-1); end
    endfunction

    always @(negedge clk) begin
        if (running && resetn) begin
            random_state = {random_state[30:0], random_state[31] ^
                            random_state[21] ^ random_state[1] ^ random_state[0]};
            output_ready = random_state[0] && random_state[3];
            if (!source_stalled) begin
                input_valid = (sent < COUNT) && (random_state[5] || random_state[8]);
                if (sent < COUNT) begin
                    input_data = inputs[sent];
                    input_last = sample_last(sent);
                end
            end
        end
    end

    always @(posedge clk) begin
        if (!resetn) begin
            sent = 0; received = 0; cycles = 0;
            source_stalled = 0; output_stalled = 0;
        end else if (running) begin
            cycles = cycles + 1;
            if (cycles > 150000) $fatal(1, "Timeout case %0d", case_index);
            if (output_stalled && (!output_valid ||
                {output_data, output_keep, output_last} !== held_output))
                $fatal(1, "Unstable output under backpressure");
            if (output_valid && output_ready) begin
                if (received >= sent) $fatal(1, "Stale or duplicate output");
                if (output_data !== expected[received])
                    $fatal(1, "Case %0d sample %0d: actual %h expected %h",
                           case_index, received, output_data, expected[received]);
                if (output_keep !== 4'hf || output_last !== sample_last(received))
                    $fatal(1, "Sideband mismatch");
                received = received + 1;
            end
            if (input_valid && input_ready) sent = sent + 1;
            source_stalled = input_valid && !input_ready;
            output_stalled = output_valid && !output_ready;
            held_output = {output_data, output_keep, output_last};
        end
    end

    initial begin
        $readmemh("ratios.hex", ratios);
        for (case_index = 0; case_index < 6; case_index = case_index + 1) begin
            @(negedge clk);
            running = 0; resetn = 0; input_valid = 0; output_ready = 0;
            ratio_q16 = ratios[case_index];
            $readmemh($sformatf("case%0d_input.hex", case_index), inputs);
            $readmemh($sformatf("case%0d_expected.hex", case_index), expected);
            repeat (3) @(negedge clk);
            resetn = 1; running = 1;
            wait (received == COUNT);
            @(negedge clk);
            running = 0; input_valid = 0; output_ready = 1;
            repeat (4) @(negedge clk);
            if (output_valid) $fatal(1, "Extra output after drain");
            $display("Case %0d ratio_q16=%0d: 4096 exact samples, cycles=%0d",
                     case_index, ratio_q16, cycles);
        end

        // Hold one unconsumed result and reset; no old valid may escape.
        ratio_q16 = 65536; output_ready = 0;
        input_data = 32'hffff8000; input_valid = 1;
        wait (input_ready);
        @(negedge clk); input_valid = 0;
        wait (output_valid);
        @(negedge clk); resetn = 0;
        repeat (3) @(negedge clk);
        if (output_valid || input_ready) $fatal(1, "Pending-output reset failed");
        resetn = 1;
        wait (input_ready);
        @(negedge clk);
        if (output_valid) $fatal(1, "Stale valid after clear");
        $display("PASS: 24576 exact samples, random stalls, TLAST, RAM/phase wraps, reset");
        $finish;
    end
    initial begin
        #20000000;
        $fatal(1, "Global simulation watchdog");
    end
endmodule

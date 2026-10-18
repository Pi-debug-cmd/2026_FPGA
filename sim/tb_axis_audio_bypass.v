`timescale 1ns/1ps
module tb_axis_audio_bypass;
    reg clk = 0;
    always #5 clk = !clk;
    reg resetn = 0;
    reg [31:0] input_data = 0;
    reg [3:0] input_keep = 4'hf;
    reg input_last = 0;
    reg input_valid = 0;
    wire input_ready;
    wire [31:0] output_data;
    wire [3:0] output_keep;
    wire output_last, output_valid;
    reg output_ready = 0;
    integer sent = 0;
    integer received = 0;
    integer cycles = 0;
    reg running = 0;
    reg source_stalled = 0;
    reg output_stalled = 0;
    reg [36:0] held_output = 0;
    reg [31:0] random_state = 32'h20261009;

    axis_audio_bypass dut (
        .aclk(clk), .aresetn(resetn),
        .s_axis_tdata(input_data), .s_axis_tkeep(input_keep),
        .s_axis_tlast(input_last), .s_axis_tvalid(input_valid),
        .s_axis_tready(input_ready), .m_axis_tdata(output_data),
        .m_axis_tkeep(output_keep), .m_axis_tlast(output_last),
        .m_axis_tvalid(output_valid), .m_axis_tready(output_ready)
    );

    function [31:0] sample_word;
        input integer index;
        reg signed [15:0] pcm;
        begin
            case (index % 5)
                0: pcm = -32768;
                1: pcm = -1;
                2: pcm = 0;
                3: pcm = 1;
                default: pcm = 32767;
            endcase
            sample_word = {{16{pcm[15]}}, pcm};
        end
    endfunction

    function sample_last;
        input integer index;
        begin
            sample_last = (index % 37 == 36) || (index == 511);
        end
    endfunction

    // Drive only on falling edges, hold upstream payload after a stalled cycle.
    always @(negedge clk) begin
        if (running && resetn) begin
            random_state = {random_state[30:0],
                            random_state[31] ^ random_state[21] ^
                            random_state[1] ^ random_state[0]};
            output_ready = random_state[0] || random_state[3];
            if (!source_stalled) begin
                input_valid = (sent < 512) && (random_state[5] || random_state[8]);
                input_data = sample_word(sent);
                input_last = sample_last(sent);
                input_keep = 4'hf;
            end
        end
    end

    always @(posedge clk) begin
        if (!resetn) begin
            sent = 0;
            received = 0;
            cycles = 0;
            source_stalled = 0;
            output_stalled = 0;
        end else if (running) begin
            cycles = cycles + 1;
            if (cycles > 10000) $fatal(1, "Timeout");
            if (output_stalled && (!output_valid ||
                {output_data, output_keep, output_last} !== held_output))
                $fatal(1, "Output changed under backpressure");
            if (output_valid && output_ready) begin
                if (received >= sent) $fatal(1, "Unaccepted input or stale output");
                if (output_data !== sample_word(received) || output_keep !== 4'hf ||
                    output_last !== sample_last(received))
                    $fatal(1, "Payload/sideband mismatch at sample %0d", received);
                received = received + 1;
            end
            if (input_valid && input_ready) sent = sent + 1;
            source_stalled = input_valid && !input_ready;
            output_stalled = output_valid && !output_ready;
            held_output = {output_data, output_keep, output_last};
        end
    end

    initial begin
        repeat (4) @(negedge clk);
        resetn = 1;
        running = 1;
        wait (received == 512);
        @(negedge clk);
        running = 0;
        input_valid = 0;
        output_ready = 1;
        repeat (3) @(negedge clk);
        if (output_valid) $fatal(1, "Extra output after drain");

        // Put a word in the register, stall it, then synchronously reset it away.
        output_ready = 0;
        input_valid = 1;
        input_data = 32'h12345678;
        @(negedge clk);
        input_valid = 0;
        if (!output_valid) $fatal(1, "Reset test did not create pending data");
        resetn = 0;
        repeat (3) @(negedge clk);
        if (output_valid || input_ready) $fatal(1, "Reset failed");
        resetn = 1;
        running = 1;
        wait (received == 512);
        @(negedge clk);
        running = 0;
        input_valid = 0;
        output_ready = 1;
        repeat (3) @(negedge clk);
        if (output_valid) $fatal(1, "Extra output after second drain");
        $display("PASS: 1024 samples, signed boundaries, random stalls, TLAST, pending reset");
        $finish;
    end
endmodule

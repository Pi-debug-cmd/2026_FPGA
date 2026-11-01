`timescale 1ns/1ps
// PCM16 in sign-extended 32-bit words. Fixed ratio_q16 for one armed run.
// 1024-sample delay sweep, 2048 PCM16 RAM, Q16 phase and weights.
module axis_pitch_shift (
    input wire aclk,
    input wire aresetn,
    input wire [17:0] ratio_q16,
    input wire [31:0] s_axis_tdata,
    input wire [3:0] s_axis_tkeep,
    input wire s_axis_tlast,
    input wire s_axis_tvalid,
    output wire s_axis_tready,
    output reg [31:0] m_axis_tdata,
    output reg [3:0] m_axis_tkeep,
    output reg m_axis_tlast,
    output reg m_axis_tvalid,
    input wire m_axis_tready
);
    localparam CLEAR = 4'd0, IDLE = 4'd1, READ_A0 = 4'd2,
               READ_B0 = 4'd3, READ_A1 = 4'd4, READ_B1 = 4'd5,
               CAPTURE_B1 = 4'd6, MULTIPLY_TAPS = 4'd7,
               INTERPOLATE = 4'd8, MULTIPLY_BLEND = 4'd9,
               BLEND = 4'd10, OUTPUT_WORD = 4'd11;
    reg [3:0] state = CLEAR;
    reg [10:0] clear_index = 0;
    reg [10:0] write_index = 0;
    reg [25:0] phase = 0;
    wire [25:0] other_phase = phase ^ 26'h2000000;
    reg [10:0] address0, address1;
    reg [17:0] recent_weight, older_weight, first_weight, second_weight;
    reg signed [15:0] a0, b0, a1, b1, tap0, tap1;
    (* keep = "true" *) reg signed [33:0] product_a0, product_b0, product_a1, product_b1;
    (* keep = "true" *) reg signed [33:0] product_first, product_second;
    reg [3:0] saved_keep;
    reg saved_last;

    wire signed [15:0] read_data;
    reg [10:0] read_address;
    wire valid_ratio = ratio_q16 >= 18'd32768 && ratio_q16 <= 18'd131072;
    assign s_axis_tready = aresetn && state == IDLE && valid_ratio;
    wire write_enable = aresetn && (state == CLEAR || (s_axis_tvalid && s_axis_tready));
    wire [10:0] write_address = state == CLEAR ? clear_index : write_index;
    wire [15:0] write_data = state == CLEAR ? 16'd0 : s_axis_tdata[15:0];

    // Clearing takes 2048 clocks; no stream input is accepted until it finishes.
    (* keep_hierarchy = "yes" *) pcm_delay_ram delay_ram (
        .aclk(aclk), .write_enable(write_enable),
        .write_address(write_address), .write_data(write_data),
        .read_address(read_address), .read_data(read_data)
    );

    always @* begin
        case (state)
            READ_A0: read_address = address0;
            READ_B0: read_address = address0 - 11'd1;
            READ_A1: read_address = address1;
            default: read_address = address1 - 11'd1;
        endcase
    end

    wire [17:0] phase_weight = !phase[25] ? {2'b0, phase[24:9]}
                                : 18'd131072 - {1'b0, phase[25:9]};
    wire signed [33:0] sum_first_tap = product_a0 + product_b0;
    wire signed [33:0] sum_second_tap = product_a1 + product_b1;
    wire signed [33:0] sum_blend = product_first + product_second;
    wire signed [15:0] mixed_sample = sum_blend >>> 16;
    always @(posedge aclk) begin
        if (!aresetn) begin
            state <= CLEAR;
            clear_index <= 0;
            write_index <= 0;
            phase <= 0;
            m_axis_tvalid <= 0;
            m_axis_tdata <= 0;
            m_axis_tkeep <= 0;
            m_axis_tlast <= 0;
        end else begin
            case (state)
                CLEAR: begin
                    if (clear_index == 2047) begin
                        clear_index <= 0;
                        state <= IDLE;
                    end else clear_index <= clear_index + 11'd1;
                end
                IDLE: if (s_axis_tvalid && s_axis_tready) begin
                    saved_keep <= s_axis_tkeep;
                    saved_last <= s_axis_tlast;
                    write_index <= write_index + 11'd1;
                    if (ratio_q16 == 18'd65536) begin
                        m_axis_tdata <= {{16{s_axis_tdata[15]}}, s_axis_tdata[15:0]};
                        m_axis_tkeep <= s_axis_tkeep;
                        m_axis_tlast <= s_axis_tlast;
                        m_axis_tvalid <= 1;
                        state <= OUTPUT_WORD;
                    end else begin
                        address0 <= write_index - 11'd2 - {1'b0, phase[25:16]};
                        address1 <= write_index - 11'd2 - {1'b0, other_phase[25:16]};
                        recent_weight <= 18'd65536 - {2'b00, phase[15:0]};
                        older_weight <= {2'b00, phase[15:0]};
                        first_weight <= phase_weight;
                        second_weight <= 18'd65536 - phase_weight;
                        phase <= phase + 26'd65536 - {8'b0, ratio_q16};
                        state <= READ_A0;
                    end
                end
                READ_A0: state <= READ_B0;
                READ_B0: begin a0 <= read_data; state <= READ_A1; end
                READ_A1: begin b0 <= read_data; state <= READ_B1; end
                READ_B1: begin a1 <= read_data; state <= CAPTURE_B1; end
                CAPTURE_B1: begin b1 <= read_data; state <= MULTIPLY_TAPS; end
                MULTIPLY_TAPS: begin
                    product_a0 <= a0 * $signed(recent_weight);
                    product_b0 <= b0 * $signed(older_weight);
                    product_a1 <= a1 * $signed(recent_weight);
                    product_b1 <= b1 * $signed(older_weight);
                    state <= INTERPOLATE;
                end
                INTERPOLATE: begin
                    tap0 <= sum_first_tap >>> 16;
                    tap1 <= sum_second_tap >>> 16;
                    state <= MULTIPLY_BLEND;
                end
                MULTIPLY_BLEND: begin
                    product_first <= tap0 * $signed(first_weight);
                    product_second <= tap1 * $signed(second_weight);
                    state <= BLEND;
                end
                BLEND: begin
                    m_axis_tdata <= {{16{mixed_sample[15]}}, mixed_sample};
                    m_axis_tkeep <= saved_keep;
                    m_axis_tlast <= saved_last;
                    m_axis_tvalid <= 1;
                    state <= OUTPUT_WORD;
                end
                OUTPUT_WORD: if (m_axis_tready) begin
                    m_axis_tvalid <= 0;
                    state <= IDLE;
                end
                default: state <= CLEAR;
            endcase
        end
    end
endmodule

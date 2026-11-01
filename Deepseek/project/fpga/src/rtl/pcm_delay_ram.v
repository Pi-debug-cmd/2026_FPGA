`timescale 1ns/1ps
// Isolated simple dual-port synchronous RAM to preserve BRAM inference.
module pcm_delay_ram (
    input wire aclk,
    input wire write_enable,
    input wire [10:0] write_address,
    input wire [15:0] write_data,
    input wire [10:0] read_address,
    output reg signed [15:0] read_data
);
    (* ram_style = "block" *) reg [15:0] memory [0:2047];
    always @(posedge aclk) begin
        if (write_enable)
            memory[write_address] <= write_data;
        read_data <= memory[read_address];
    end
endmodule

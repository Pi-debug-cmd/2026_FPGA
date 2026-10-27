`timescale 1ns/1ps
// One-entry AXI-Stream register; payload and sidebands survive backpressure.
module axis_audio_bypass (
    input wire aclk,
    input wire aresetn,
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
    assign s_axis_tready = aresetn && (!m_axis_tvalid || m_axis_tready);

    always @(posedge aclk) begin
        if (!aresetn) begin
            m_axis_tvalid <= 1'b0;
            m_axis_tdata <= 32'b0;
            m_axis_tkeep <= 4'b0;
            m_axis_tlast <= 1'b0;
        end else if (s_axis_tready) begin
            m_axis_tvalid <= s_axis_tvalid;
            if (s_axis_tvalid) begin
                m_axis_tdata <= s_axis_tdata;
                m_axis_tkeep <= s_axis_tkeep;
                m_axis_tlast <= s_axis_tlast;
            end
        end
    end
endmodule

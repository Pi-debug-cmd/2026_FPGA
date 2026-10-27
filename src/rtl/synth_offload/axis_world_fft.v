// One DMA packet = 64-bit config header followed by N complex float32 samples.
// Header low24 is XFFT config (NFFT[4:0], forward bit8); no output header.
module axis_world_fft (
  input wire aclk, input wire aresetn,
  input wire [63:0] s_axis_tdata, input wire s_axis_tvalid,
  output wire s_axis_tready, input wire s_axis_tlast,
  output wire [63:0] m_axis_tdata, output wire m_axis_tvalid,
  input wire m_axis_tready, output wire m_axis_tlast,
  output reg protocol_error
);
  localparam HEADER=0, CONFIG=1, DATA=2, DRAIN=3;
  reg [1:0] state;
  reg [23:0] config_data;
  reg [11:0] count, last_index;
  wire config_ready, input_ready;
  wire event_unexpected, event_missing;
  assign s_axis_tready = state==HEADER || (state==DATA && input_ready);
  always @(posedge aclk) begin
    if (!aresetn) begin
      state<=HEADER; config_data<=0; count<=0; last_index<=0; protocol_error<=0;
    end else begin
      if (event_unexpected || event_missing) protocol_error<=1;
      case(state)
        HEADER: if (s_axis_tvalid && s_axis_tready) begin
          if ((s_axis_tdata[4:0]!=10 && s_axis_tdata[4:0]!=11) || s_axis_tlast)
            protocol_error<=1;
          config_data<=s_axis_tdata[23:0];
          last_index<=s_axis_tdata[4:0]==10 ? 12'd1023 : 12'd2047;
          count<=0; state<=CONFIG;
        end
        CONFIG: if (config_ready) state<=DATA;
        DATA: if (s_axis_tvalid && s_axis_tready) begin
          if (s_axis_tlast != (count==last_index)) protocol_error<=1;
          if (count==last_index) state<=DRAIN;
          else count<=count+1;
        end
        DRAIN: if (m_axis_tvalid && m_axis_tready && m_axis_tlast) state<=HEADER;
      endcase
    end
  end
  world_fft_core core (
    .aclk(aclk), .aresetn(aresetn),
    .s_axis_config_tdata(config_data), .s_axis_config_tvalid(state==CONFIG),
    .s_axis_config_tready(config_ready),
    .s_axis_data_tdata(s_axis_tdata), .s_axis_data_tvalid(s_axis_tvalid && state==DATA),
    .s_axis_data_tready(input_ready), .s_axis_data_tlast(count==last_index),
    .m_axis_data_tdata(m_axis_tdata), .m_axis_data_tvalid(m_axis_tvalid),
    .m_axis_data_tready(m_axis_tready), .m_axis_data_tlast(m_axis_tlast),
    .event_tlast_unexpected(event_unexpected), .event_tlast_missing(event_missing),
    .event_frame_started(), .event_status_channel_halt(),
    .event_data_in_channel_halt(), .event_data_out_channel_halt()
  );
endmodule

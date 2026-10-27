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
  reg [11:0] count, last_index, output_count;
  reg real_input, high_half;
  wire config_ready, input_ready;
  wire event_unexpected, event_missing;
  wire [63:0] core_output;
  wire core_valid, core_last;
  wire keep_output = !real_input || output_count <= (last_index >> 1)+1;
  assign m_axis_tdata=core_output;
  assign m_axis_tvalid=core_valid && keep_output;
  assign m_axis_tlast=real_input ? output_count==(last_index >> 1)+1 : core_last;
  assign s_axis_tready = state==HEADER || (state==DATA && input_ready && (!real_input || high_half));
  always @(posedge aclk) begin
    if (!aresetn) begin
      state<=HEADER; config_data<=0; count<=0; last_index<=0; protocol_error<=0;
      real_input<=0;high_half<=0;output_count<=0;
    end else begin
      if (event_unexpected || event_missing) protocol_error<=1;
      if(core_valid && (m_axis_tready || !keep_output)) output_count<=output_count+1;
      case(state)
        HEADER: if (s_axis_tvalid && s_axis_tready) begin
          if ((s_axis_tdata[4:0]!=10 && s_axis_tdata[4:0]!=11) || s_axis_tlast)
            protocol_error<=1;
          // bit9 is our compact real-input flag, not part of the IP config.
          config_data<=s_axis_tdata[23:0] & 24'hfffdff;
          real_input<=s_axis_tdata[9];high_half<=0;output_count<=0;
          last_index<=s_axis_tdata[4:0]==10 ? 12'd1023 : 12'd2047;
          count<=0; state<=CONFIG;
        end
        CONFIG: if (config_ready) state<=DATA;
        DATA: if (s_axis_tvalid && input_ready) begin
          if ((!real_input || high_half) && (s_axis_tlast != (count==last_index))) protocol_error<=1;
          if(real_input) high_half<=!high_half;
          if (count==last_index) state<=DRAIN;
          else count<=count+1;
        end
        DRAIN: if (core_valid && (m_axis_tready || !keep_output) && core_last) state<=HEADER;
      endcase
    end
  end
  world_fft_core core (
    .aclk(aclk), .aresetn(aresetn),
    .s_axis_config_tdata(config_data), .s_axis_config_tvalid(state==CONFIG),
    .s_axis_config_tready(config_ready),
    .s_axis_data_tdata(real_input ? {32'b0,(high_half?s_axis_tdata[63:32]:s_axis_tdata[31:0])} : s_axis_tdata), .s_axis_data_tvalid(s_axis_tvalid && state==DATA),
    .s_axis_data_tready(input_ready), .s_axis_data_tlast(count==last_index),
    .m_axis_data_tdata(core_output), .m_axis_data_tvalid(core_valid),
    .m_axis_data_tready(m_axis_tready || !keep_output), .m_axis_data_tlast(core_last),
    .event_tlast_unexpected(event_unexpected), .event_tlast_missing(event_missing),
    .event_frame_started(), .event_status_channel_halt(),
    .event_data_in_channel_halt(), .event_data_out_channel_halt()
  );
endmodule

`timescale 1ns/1ps
// M1 out-of-context wrapper: only the two xfft instances, nothing else, so the
// FFT core resource/timing numbers are not polluted by the STFT frame engine.
module fft_pair (
    input  wire        aclk,
    input  wire        aresetn,

    input  wire [47:0] fwd_s_tdata,
    input  wire        fwd_s_tvalid,
    output wire        fwd_s_tready,
    input  wire        fwd_s_tlast,
    input  wire [7:0]  fwd_cfg_tdata,
    input  wire        fwd_cfg_tvalid,
    output wire        fwd_cfg_tready,
    output wire [79:0] fwd_m_tdata,
    output wire        fwd_m_tvalid,
    input  wire        fwd_m_tready,
    output wire        fwd_m_tlast,

    input  wire [63:0] inv_s_tdata,
    input  wire        inv_s_tvalid,
    output wire        inv_s_tready,
    input  wire        inv_s_tlast,
    input  wire [7:0]  inv_cfg_tdata,
    input  wire        inv_cfg_tvalid,
    output wire        inv_cfg_tready,
    output wire [95:0] inv_m_tdata,
    output wire        inv_m_tvalid,
    input  wire        inv_m_tready,
    output wire        inv_m_tlast
);

    fft_fwd u_fwd (
        .aclk(aclk), .aresetn(aresetn),
        .s_axis_config_tdata(fwd_cfg_tdata),
        .s_axis_config_tvalid(fwd_cfg_tvalid),
        .s_axis_config_tready(fwd_cfg_tready),
        .s_axis_data_tdata(fwd_s_tdata),
        .s_axis_data_tvalid(fwd_s_tvalid),
        .s_axis_data_tready(fwd_s_tready),
        .s_axis_data_tlast(fwd_s_tlast),
        .m_axis_data_tdata(fwd_m_tdata),
        .m_axis_data_tvalid(fwd_m_tvalid),
        .m_axis_data_tready(fwd_m_tready),
        .m_axis_data_tlast(fwd_m_tlast),
        .event_frame_started(), .event_tlast_unexpected(), .event_tlast_missing(),
        .event_status_channel_halt(), .event_data_in_channel_halt(),
        .event_data_out_channel_halt()
    );

    fft_inv u_inv (
        .aclk(aclk), .aresetn(aresetn),
        .s_axis_config_tdata(inv_cfg_tdata),
        .s_axis_config_tvalid(inv_cfg_tvalid),
        .s_axis_config_tready(inv_cfg_tready),
        .s_axis_data_tdata(inv_s_tdata),
        .s_axis_data_tvalid(inv_s_tvalid),
        .s_axis_data_tready(inv_s_tready),
        .s_axis_data_tlast(inv_s_tlast),
        .m_axis_data_tdata(inv_m_tdata),
        .m_axis_data_tvalid(inv_m_tvalid),
        .m_axis_data_tready(inv_m_tready),
        .m_axis_data_tlast(inv_m_tlast),
        .event_frame_started(), .event_tlast_unexpected(), .event_tlast_missing(),
        .event_status_channel_halt(), .event_data_in_channel_halt(),
        .event_data_out_channel_halt()
    );

endmodule

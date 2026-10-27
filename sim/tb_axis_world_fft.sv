`timescale 1ns/1ps
module tb_axis_world_fft;
  reg clk=0; always #5 clk=~clk;
  reg resetn=0, valid=0, last=0;
  reg [63:0] data=0;
  wire ready, out_valid, out_last, error;
  wire [63:0] out_data;
  reg out_ready=0;
  reg [63:0] inputs[0:50000], expected[0:50000];
  integer read_count=0, cycles=0, frame_count=0;
  integer pos=0, n, i, f, frame_start, sent, wanted;
  reg [31:0] random_state=32'h20261027;
  string input_file, output_file;
  axis_world_fft dut(.aclk(clk),.aresetn(resetn),
    .s_axis_tdata(data),.s_axis_tvalid(valid),.s_axis_tready(ready),.s_axis_tlast(last),
    .m_axis_tdata(out_data),.m_axis_tvalid(out_valid),.m_axis_tready(out_ready),
    .m_axis_tlast(out_last),.protocol_error(error));
  always @(negedge clk) begin
    random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
    // First half runs without output backpressure, second half exercises it.
    out_ready=resetn && (frame_count<15 || random_state[3:0]!=0);
  end
  always @(posedge clk) if (resetn) begin
    cycles<=cycles+1;
    if (cycles>1000000) $fatal(1,"FFT timeout");
    if (error) $fatal(1,"FFT protocol error");
    if (out_valid && out_ready) begin
      if (out_data !== expected[read_count])
        $fatal(1,"FFT mismatch word %0d got %h expected %h",read_count,out_data,expected[read_count]);
      read_count<=read_count+1;
      if (out_last) frame_count<=frame_count+1;
    end
  end
  task send_word(input [63:0] word, input bit is_last);
    begin
      @(negedge clk);data=word;valid=1;last=is_last;
      @(posedge clk);
      while (!ready) @(posedge clk);
    end
  endtask
  initial begin
    input_file="input.mem";output_file="output.mem";
    i=$value$plusargs("IN=%s",input_file);
    i=$value$plusargs("OUT=%s",output_file);
    $readmemh(input_file,inputs);$readmemh(output_file,expected);
    repeat(12) @(negedge clk);resetn=1;
    for(f=0;f<30;f=f+1) begin
      n=1<<inputs[pos][4:0];frame_start=cycles;wanted=read_count+n;
      send_word(inputs[pos],0);pos=pos+1;
      for(i=0;i<n;i=i+1) begin
        if (f>=15 && random_state[5:4]==0) begin
          @(negedge clk);valid=0;
        end
        send_word(inputs[pos],i==n-1);pos=pos+1;
      end
      @(negedge clk);valid=0;last=0;
      wait(frame_count==f+1);
      if(read_count!=wanted) $fatal(1,"FFT frame length");
      $display("FFT_FRAME frame=%0d n=%0d cycles=%0d",f,n,cycles-frame_start);
      repeat(3) @(negedge clk);
    end
    $display("FFT_STREAM_PASS frames=%0d words=%0d",frame_count,read_count);$finish;
  end
endmodule

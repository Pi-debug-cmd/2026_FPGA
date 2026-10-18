`timescale 1ns/1ps
// ============================================================================
// 1024 x 36 位单读单写（SDP）块 RAM 封装 —— WORLD 合成卸载 IFFT 核的数据缓冲
//
// 采用 Vivado 最稳妥的简单双口（Simple Dual Port）推断模板：
//   写端口 waddr/wdata/we，读端口 raddr/dout，读数据寄存输出（同步读）。
//   读写同址时输出旧数据（READ_FIRST，非阻塞赋值语义）。
// 1024x36 = 36 Kb，综合应映射为 1 个 RAMB36（=2 个 RAMB18）。
//
// 为什么不用真双口（TDP）：在 Vivado 2026.1 下，本核需要的“同拍 2 读 + 2 写”
// 无法由单个 36 Kb BRAM（每拍最多 2 次访问）实现，推断会退化成 36864 个
// 触发器 + 数万 LUT。改用 1R1W 后，蝶形按“读 A / 读 B / 乘 / 舍入 / 写 A /
// 写 B”6 拍串行完成，资源回到 1 个 RAMB36。
// ============================================================================
module dpram_1024x36 (
    input  wire        clk,
    input  wire        we,
    input  wire [9:0]  waddr,
    input  wire [35:0] wdata,
    input  wire [9:0]  raddr,
    output reg  [35:0] dout
);
    (* ram_style = "block" *) reg [35:0] mem [0:1023];

    always @(posedge clk) begin
        if (we) mem[waddr] <= wdata;
        dout <= mem[raddr];
    end
endmodule

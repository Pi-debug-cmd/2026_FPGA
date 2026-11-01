`timescale 1ns / 1ps
module my_iobuf (
    input  wire I,
    input  wire T,
    output wire O,
    inout  wire IO
);
    IOBUF u_iobuf (
        .I(I),
        .T(T),
        .O(O),
        .IO(IO)
    );
endmodule

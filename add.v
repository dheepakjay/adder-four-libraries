// Two designs: a 1-bit half adder and an 8-bit adder with two 8-bit inputs
module ha(input a, b, output s, c);
  assign s = a ^ b;
  assign c = a & b;
endmodule

module add8(input [7:0] a, b, output [8:0] s);
  assign s = a + b;
endmodule

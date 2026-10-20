// Lower-bound building block for the Coron et al. 2023 arithmetic (mod-q product / Fermat) comparison family:
// one registered, UNMASKED 12 x 12-bit integer multiplier (no modular reduction). Any masked mod-q multiplication of
// 3-share values needs 9 such partial products plus reduction and refresh, so 9 x area(mul12) is a lower bound.
module mul12_lane (input wire clk, input wire [11:0] a, b, output reg [23:0] p);
  reg [11:0] ar, br;
  always @(posedge clk) begin ar <= a; br <= b; p <= ar * br; end
endmodule

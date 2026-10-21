// PROLEAD test fixture (not part of the design under test): turns the unshared PROLEAD group value tb_x (12 bits,
// fixed or random) and two fresh 32-bit uniform words into a registered 3-share arithmetic sharing mod q = 3329:
//   x1 = floor(R1 * q / 2^32), x2 = floor(R2 * q / 2^32)   (each within statistical distance < 2^-20 of uniform on Z_q)
//   x0 = (x mod q) - x1 - x2  (mod q)
// Every signal of this module is prefixed tb_ and excluded from probe placement; its outputs are registers, so
// glitch-extended probes inside the lane stop at them.
module tb_gen (input wire clk, input wire [11:0] tb_x, input wire [31:0] tb_r1, input wire [31:0] tb_r2,
               output reg [11:0] tb_x0, output reg [11:0] tb_x1, output reg [11:0] tb_x2);
  wire [11:0] tb_xr = tb_x >= 12'd3329 ? tb_x - 12'd3329 : tb_x;
  wire [43:0] tb_p1 = tb_r1 * 44'd3329, tb_p2 = tb_r2 * 44'd3329;
  wire [11:0] tb_m1 = tb_p1[43:32], tb_m2 = tb_p2[43:32];
  wire [13:0] tb_s = {2'b0, tb_xr} + 14'd6658 - tb_m1 - tb_m2;          // in (0, 3q)
  wire [13:0] tb_t = tb_s >= 14'd6658 ? tb_s - 14'd6658 : tb_s >= 14'd3329 ? tb_s - 14'd3329 : tb_s;
  always @(posedge clk) begin tb_x0 <= tb_t[11:0]; tb_x1 <= tb_m1; tb_x2 <= tb_m2; end
endmodule

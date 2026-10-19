// Trivium, 64 keystream bits per cycle (state s[0] = s1 ... s[287] = s288); seeded via load/seed.
module trivium64 (input wire clk, input wire load, input wire [287:0] seed, output reg [63:0] z);
  reg [287:0] s;
  function [351:0] step64(input [287:0] st);   // {new state, 64 keystream bits}
    integer i; reg [287:0] x; reg [63:0] o; reg t1, t2, t3;
    begin x = st;
      for (i = 0; i < 64; i = i + 1) begin
        t1 = x[65] ^ x[92]; t2 = x[161] ^ x[176]; t3 = x[242] ^ x[287]; o[i] = t1 ^ t2 ^ t3;
        t1 = t1 ^ (x[90] & x[91]) ^ x[170]; t2 = t2 ^ (x[174] & x[175]) ^ x[263]; t3 = t3 ^ (x[285] & x[286]) ^ x[68];
        x = {x[286:177], t2, x[175:93], t1, x[91:0], t3};
      end
      step64 = {x, o}; end
  endfunction
  wire [351:0] nx = step64(s);
  always @(posedge clk) if (load) s <= seed; else begin s <= nx[351:64]; z <= nx[63:0]; end
endmodule

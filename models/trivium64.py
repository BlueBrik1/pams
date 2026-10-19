#!/usr/bin/env python3
"""Trivium keystream generator, 64 bits per cycle (eSTREAM; De Canniere-Preneel), as a randomness-source cost model
for the masking gadgets. Key/IV loading and initialisation rounds are omitted (state seeded through a load port);
checked against a bit-serial Python reference.  usage: python3 -I trivium64.py   -> ../rtl/trivium64.v"""
import random, subprocess, tempfile
from pathlib import Path
def ref(state, n):
    s = list(state); out = []
    for _ in range(n):
        t1 = s[65] ^ s[92]; t2 = s[161] ^ s[176]; t3 = s[242] ^ s[287]; out.append(t1 ^ t2 ^ t3)
        t1 ^= (s[90] & s[91]) ^ s[170]; t2 ^= (s[174] & s[175]) ^ s[263]; t3 ^= (s[285] & s[286]) ^ s[68]
        s = [t3] + s[0:92] + [t1] + s[93:176] + [t2] + s[177:287]
    return out, s
V = '''// Trivium, 64 keystream bits per cycle (state s[0] = s1 ... s[287] = s288); seeded via load/seed.
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
'''
if __name__ == '__main__':
    out = Path(__file__).resolve().parents[1] / 'rtl' / 'trivium64.v'; out.write_text(V)
    rng = random.Random(5); st = [rng.getrandbits(1) for _ in range(288)]; exp, _ = ref(st, 64 * 4)
    seed = ''.join(str(b) for b in reversed(st))
    tb = f'''module tb; reg clk = 0; always #5 clk = ~clk; reg load = 1; wire [63:0] z; reg [287:0] sd = 288'b{seed};
  trivium64 u (.clk(clk), .load(load), .seed(sd), .z(z)); integer i;
  initial begin @(negedge clk); load = 0; for (i = 0; i < 4; i = i + 1) begin @(negedge clk); $display("%b", z); end $finish; end
endmodule'''
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / 'tb.v').write_text(tb)
        subprocess.run(['iverilog', '-o', f'{td}/a', f'{td}/tb.v', str(out)], check=True)
        lines = subprocess.run(['vvp', '-n', f'{td}/a'], capture_output=True, text=True).stdout.split()
    lines = [l for l in lines if set(l) <= set('01') and len(l) == 64]
    got = [int(b) for l in lines for b in reversed(l)]
    assert got == exp, 'trivium mismatch'
    print('PASS trivium64: 256 keystream bits match the bit-serial reference')

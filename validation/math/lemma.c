// Exhaustive check of the share-wise modulus-switching lemma over ALL canonical 3-share triples (x0, x1, x2) in
// [0, q)^3: with F_K(v) = floor(v 2^K / q) and x = (x0 + x1 + x2) mod q,
//     j := (F_K(x) - F_K(x0) - F_K(x1) - F_K(x2)) mod 2^K   must lie in {0, 1, 2}.
// Also records which (x, j) pairs are reachable (written to reach_K<K>.bin, q*3 bytes) for the K = 13 lower bound.
// Build: gcc -O3 -fopenmp lemma.c -o lemma ; run: ./lemma K
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define Q 3329
int main(int argc, char **argv) {
  int K = atoi(argv[1]); uint64_t M = (1ull << K) - 1;
  static uint64_t F[Q]; for (int v = 0; v < Q; v++) F[v] = ((uint64_t)v << K) / Q;
  static unsigned char reach[Q][3]; uint64_t bad = 0, total = 0;
  #pragma omp parallel for reduction(+:bad,total) schedule(dynamic)
  for (int x0 = 0; x0 < Q; x0++) {
    unsigned char loc[Q][3] = {{0}};
    for (int x1 = 0; x1 < Q; x1++) for (int x2 = 0; x2 < Q; x2++) {
      int x = (x0 + x1 + x2) % Q;
      uint64_t j = (F[x] - F[x0] - F[x1] - F[x2]) & M;
      total++;
      if (j > 2) bad++; else loc[x][j] = 1;
    }
    #pragma omp critical
    for (int x = 0; x < Q; x++) for (int j = 0; j < 3; j++) reach[x][j] |= loc[x][j];
  }
  int r[3] = {0, 0, 0}; for (int x = 0; x < Q; x++) for (int j = 0; j < 3; j++) r[j] += reach[x][j];
  printf("K=%d triples=%llu violations=%llu reachable x with j=0:%d j=1:%d j=2:%d (of %d)\n", K,
         (unsigned long long)total, (unsigned long long)bad, r[0], r[1], r[2], Q);
  char fn[64]; snprintf(fn, sizeof fn, "reach_K%d.bin", K); FILE *f = fopen(fn, "wb"); fwrite(reach, 1, sizeof reach, f); fclose(f);
  return bad != 0;
}

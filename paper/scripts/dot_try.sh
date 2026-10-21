#!/bin/bash
# try Graphviz layout variants of the two extracted gate-level figures (review only): dot_try.sh
cd "$(dirname "$0")/.."
mkdir -p _preview/dot
for v in A B C; do
  case $v in
    A) H='rankdir=LR; splines=ortho; nodesep=0.28; ranksep=0.55;' ;;
    B) H='rankdir=LR; splines=true; nodesep=0.35; ranksep=0.7;' ;;
    C) H='rankdir=LR; splines=polyline; nodesep=0.3; ranksep=0.6;' ;;
  esac
  for f in hpc2_mapped slice_bit1; do
    sed -E "0,/rankdir=LR; nodesep=[0-9.]+; ranksep=[0-9.]+;/s//$H/" figures/gates/$f.dot > _preview/dot/${f}_$v.dot
    [ $f = slice_bit1 ] && [ $v = A ] && sed -i -E 's/\[label="([abAB])"\]/[xlabel="\1"]/' _preview/dot/${f}_$v.dot
    dot -Tpng -Gdpi=110 _preview/dot/${f}_$v.dot -o _preview/dot/${f}_$v.png 2>&1 | head -3
  done
done
ls _preview/dot

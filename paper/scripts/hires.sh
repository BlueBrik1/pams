#!/bin/bash
# render selected pages at high resolution for figure-legibility review: hires.sh DPI page [page ...]
cd "$(dirname "$0")/.."
dpi=$1; shift
for p in "$@"; do bash scripts/preview.sh main.pdf _preview/hi$p "$p" "$p" "$dpi"; done
ls _preview | grep '^hi'

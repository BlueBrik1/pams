#!/bin/bash
# full-text dumps of the downloaded (untrusted) papers for reading; outputs in masked_verification/refs/
cd ~/lwe_agent_handoff/phase2
for p in danvers_2023/danvers2023 bos_2021/bos2021 danvers_2022/danvers2022 coron_2023/coron2023 shahmirzadi_2024/sh2024; do
  python3 -I pdftext.py ext/papers/$p.pdf | nl -ba > masked_verification/refs/$(basename $p).txt; wc -l masked_verification/refs/$(basename $p).txt
done

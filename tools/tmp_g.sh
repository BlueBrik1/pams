cd ~/lwe_agent_handoff/phase2/ext/papers
get() { mkdir -p "$1" && curl -s -L -m 180 -A "Mozilla/5.0" -o "$1/$2" "$3"; if [ "$(head -c 4 $1/$2)" = "%PDF" ]; then sha256sum $1/$2 >> SHA256SUMS; echo "$1 ok"; else echo "$1 FAIL"; rm -f $1/$2; fi; }
get heinz_2022 heinz2022.pdf "https://cryptojedi.org/papers/maskedkyber-20220117.pdf"
get kyber_hw_2022_1547 hw2022.pdf "https://web.archive.org/web/2024id_/https://eprint.iacr.org/2022/1547.pdf"
cd ~/lwe_agent_handoff/phase2
for p in heinz_2022/heinz2022 kyber_hw_2022_1547/hw2022; do [ -f ext/papers/$p.pdf ] && python3 -I pdftext.py ext/papers/$p.pdf | nl -ba > masked_verification/refs/$(basename $p).txt; done
cd masked_verification/tools
python3 -I grep_refs.py heinz2022 "interval" "decompress" "power-of-two" | cut -c1-900 | head -12
echo ======= HW2022; python3 -I grep_refs.py hw2022 "comparison" "interval" | cut -c1-700 | head -8
echo ======= X2X; python3 -I grep_refs.py x2x "comparison" "Kyber" "power-of-two" | cut -c1-700 | head -10

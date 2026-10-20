# Fetch accessible masked Kyber / ML-KEM implementations for the prior-art code review (read-only data).
D=~/lwe_agent_handoff/phase2/ext/priorart; mkdir -p $D; cd $D
while read name url; do
  [ -d "$name" ] || git clone -q --depth 1 "$url" "$name" 2>/dev/null || echo "FAILED $name $url"
  [ -d "$name" ] && echo "$name $(git -C $name log -1 --format='%h %ci') $url"
done <<'EOF'
hope-mlkem https://github.com/HWSec-CSIC/hope-mlkem
mkm4 https://github.com/masked-kyber-m4/mkm4
revisiting-masked-comparison https://github.com/KULeuven-COSIC/Revisiting-Masked-Comparison
ho-kyber-coron https://github.com/fragerar/HO_Kyber
adams-bridge https://github.com/chipsalliance/adams-bridge
EOF

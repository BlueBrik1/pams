# Download primary sources (data only) and extract text with pdftotext. Usage: get_papers.sh name url [name url ...]
D=~/lwe_agent_handoff/phase2/ext/priorart/papers; mkdir -p $D; cd $D
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
while [ $# -ge 2 ]; do
  n=$1; u=$2; shift 2
  [ -s $n.pdf ] || curl -sSL -A "$UA" -o $n.pdf "$u"
  if head -c 5 $n.pdf | grep -q '%PDF'; then LD_LIBRARY_PATH=~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot/usr/lib/x86_64-linux-gnu ~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot/usr/bin/pdftotext -layout $n.pdf $n.txt 2>/dev/null; echo "$n OK $(wc -c < $n.txt) chars  $(sha256sum $n.pdf | cut -c1-16)  $u"
  else echo "$n FAILED ($(head -c 60 $n.pdf | tr -d '\n'))  $u"; rm -f $n.pdf; fi
done

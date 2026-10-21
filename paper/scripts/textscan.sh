#!/bin/bash
# scan the built PDF's text for terms that must not appear; print metadata. usage: textscan.sh [pattern]
cd "$(dirname "$0")/.."
S=~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot
export LD_LIBRARY_PATH=$S/usr/lib/x86_64-linux-gnu
pat=${1:-'AI_USAGE|AI system|Claude|artificial|disclosure|AI assist|Anthropic'}
echo "matches for /$pat/:"; $S/usr/bin/pdftotext PAMS_paper.pdf - | grep -n -i -E "$pat" | head
$S/usr/bin/pdfinfo PAMS_paper.pdf | grep -E 'Author|Title|Pages'

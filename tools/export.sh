#!/bin/bash
# Export the tracked PAMS research files (phase2/masked_verification only) into a fresh directory, excluding
# regenerable layout/parasitics/netlist dumps.  usage: export.sh DEST
set -e
DEST=$1; rm -rf "$DEST"; mkdir -p "$DEST"
cd ~/lwe_agent_handoff
git ls-files phase2/masked_verification | grep -v -E '\.(def|spef)$|/final\.v$|/pnr_in\.v$|/route\.guide$|^phase2/masked_verification/refs/' > "$DEST/.filelist"
tar -cf - -T "$DEST/.filelist" | tar -xf - -C "$DEST" --strip-components=2
rm "$DEST/.filelist"
cd "$DEST"; echo "files: $(find . -type f | wc -l)  size: $(du -sh . | cut -f1)"
find . -type f -size +2M | head

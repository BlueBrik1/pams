# Resolve TCHES article ids to PDF download links, then fetch via get_papers.sh. Usage: tches_links.sh name id [name id ...]
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
args=()
while [ $# -ge 2 ]; do
  n=$1; id=$2; shift 2
  l=$(curl -sSL -A "$UA" "https://tches.iacr.org/index.php/TCHES/article/view/$id" | grep -o "article/download/$id/[0-9]*" | head -1)
  [ -n "$l" ] && args+=("$n" "https://tches.iacr.org/index.php/TCHES/$l") || echo "no link for $n $id"
done
bash "$(dirname "$0")/get_papers.sh" "${args[@]}"

#!/bin/bash
# rename-note.sh -- safely rename a note and update all wiki-link references across the vault.
# Usage: rename-note.sh "old title" "new title"
set -euo pipefail
cd "$(dirname "$0")/../.."

OLD="${1:?usage: rename-note.sh \"old title\" \"new title\"}"
NEW="${2:?usage: rename-note.sh \"old title\" \"new title\"}"

CANDIDATES=()
while IFS= read -r c; do
  CANDIDATES+=("$c")
done < <(find . -name "${OLD}.md" -not -path './.git/*' 2>/dev/null)

if [ "${#CANDIDATES[@]}" -eq 0 ]; then
  echo "Not found: ${OLD}.md" >&2
  exit 1
fi

if [ "${#CANDIDATES[@]}" -gt 1 ]; then
  echo "Refusing to rename: ${#CANDIDATES[@]} files named ${OLD}.md exist (this vault allows duplicate structural filenames -- see CLAUDE.md Wiki-Links section). Specify the full path instead of a bare title:" >&2
  printf '  %s\n' "${CANDIDATES[@]}" >&2
  exit 1
fi

OLDFILE="${CANDIDATES[0]}"
DIR=$(dirname "$OLDFILE")
NEWFILE="${DIR}/${NEW}.md"

git mv "$OLDFILE" "$NEWFILE"

# Update all wiki-link references, both bare [[old title|display]] and path-qualified
# [[folder/path/old title|display]] forms (this vault resolves duplicate-prone structural
# filenames by path; unique note titles resolve bare -- see CLAUDE.md Wiki-Links section).
grep -rl -- "\[\[.*${OLD}" --include='*.md' . 2>/dev/null | while read -r f; do
  perl -pi -e "s/(\[\[(?:[^\]]*\/)?)\Q${OLD}\E(?=\\\\?\||\])/\${1}${NEW}/g" "$f"
done

echo "Renamed ${OLDFILE} -> ${NEWFILE}. Verify: rg -n '\[\[(.*/)?${OLD}(\||\])' --glob '*.md' . (should print nothing)"

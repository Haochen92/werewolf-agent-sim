#!/usr/bin/env bash
# Run one fresh-context reviewer on a portfolio page and save its findings beside the brief.
#
# Usage: review.sh <editorial|claims> <page.md> [claude|codex]
#
# editorial: text-only cold read from an empty directory, given the parent excerpt the reader
#            has already read (scripts/parent_context.py). Claude tools are disabled; Codex
#            is read-only and instructed not to use tools (not filesystem isolation).
# claims:    runs read-only in the repository with the page, the brief and the sources.
#
# Output: <page dir>/_authoring/<page stem>.review-<kind>.<cli>.<unique-run-id>.md
# Env:    DRY_RUN=1 prints the prompt instead of calling a model.
#         CLAUDE_MODEL (default opus), CODEX_BIN (default: the VS Code extension's codex, else PATH), CODEX_MODEL (default: Codex config).
set -euo pipefail

kind=${1:?usage: review.sh <editorial|claims> <page.md> [claude|codex]}
page=${2:?usage: review.sh <editorial|claims> <page.md> [claude|codex]}
cli=${3:-claude}
case $kind in editorial|claims) ;; *) echo "kind must be editorial or claims" >&2; exit 1 ;; esac
case $cli in claude|codex) ;; *) echo "cli must be claude or codex" >&2; exit 1 ;; esac

skill_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
repo=$(git -C "$skill_dir" rev-parse --show-toplevel)
page=$(realpath "$page")
[[ -f $page ]] || { echo "no such page: $page" >&2; exit 1; }
stem=$(basename "$page" .md)
authoring_dir=$(dirname "$page")/_authoring
brief=$authoring_dir/$stem.brief.md
out=$authoring_dir/$stem.review-$kind.$cli.\<run-id\>.md

# Strip authoring comments and navigation, retaining title and subtitle before the brief.
page_copy() {
  python3 - "$page" <<'PYCODE'
from pathlib import Path
import re, sys
text = re.sub(r"<!--.*?-->", "", Path(sys.argv[1]).read_text(), flags=re.S)
marker = re.search(r"^## Page copy[^\n]*$", text, flags=re.M)
if marker:
    front = text[:marker.start()]
    front = re.split(r"^## |^---\s*$", front, maxsplit=1, flags=re.M)[0]
    # Drop the whole status paragraph: a wrapped "*Level N · ... status ...*" header spans lines.
    front = "\n\n".join(para for para in re.split(r"\n\s*\n", front)
                        if not re.match(r"\s*\*Level [123]\b", para))
    text = front.strip() + "\n\n" + text[marker.end():].strip()
print(text)
PYCODE
}

case $kind in
  editorial)
    prompt=$(cat "$skill_dir/reviewers/editorial.md"; echo
             echo "WHAT THE READER HAS ALREADY READ"; echo
             python3 "$skill_dir/scripts/parent_context.py" "$page"; echo
             echo "PAGE COPY"; echo; page_copy)
    workdir=""  # an empty temp directory, made below
    ;;
  claims)
    rel_page=$(realpath --relative-to="$repo" "$page")
    rel_brief="(no brief for this page)"
    [[ -f $brief ]] && rel_brief=$(realpath --relative-to="$repo" "$brief")
    prompt=$(cat "$skill_dir/reviewers/claims.md"; echo
             echo "PAGE FILE: $rel_page"
             echo "AUTHORING BRIEF: $rel_brief")
    workdir=$repo
    ;;
  *) echo "kind must be editorial or claims" >&2; exit 1 ;;
esac

if [[ ${DRY_RUN:-0} == 1 ]]; then
  echo "# cli=$cli workdir=$workdir out=$out"
  printf '%s\n' "$prompt"
  exit 0
fi

mkdir -p "$authoring_dir"
run_dir=$(mktemp -d)
trap 'rm -rf -- "$run_dir"' EXIT
[[ -z $workdir ]] && { mkdir "$run_dir/work"; workdir=$run_dir/work; }
tmp_out=$run_dir/result
# Reserve a unique path only after successful review; failures leave no completed-review file.
case $cli in
  claude)
    model=${CLAUDE_MODEL:-opus}
    if [[ $kind == editorial ]]; then tools=(--tools ""); else tools=(--tools "Read,Grep,Glob"); fi
    (cd "$workdir" && printf '%s' "$prompt" | claude -p --model "$model" \
       "${tools[@]}" --no-session-persistence) > "$tmp_out"
    ;;
  codex)
    # The codex on PATH can be an old standalone install; prefer the VS Code extension's bundled CLI.
    if [[ -z ${CODEX_BIN:-} ]]; then
      CODEX_BIN=$(python3 - <<'PYCODE'
from pathlib import Path
bins = list(Path.home().glob('.vscode-server/extensions/openai.chatgpt-*/bin/*/codex'))
print(max(bins, key=lambda p: p.stat().st_mtime) if bins else 'codex')
PYCODE
      )
    fi
    model=${CODEX_MODEL:-Codex config default}
    model_args=(); [[ -n ${CODEX_MODEL:-} ]] && model_args=(-m "$CODEX_MODEL")
    printf '%s' "$prompt" | "${CODEX_BIN:-codex}" exec "${model_args[@]}" -s read-only \
      --skip-git-repo-check -C "$workdir" --output-last-message "$tmp_out" - > /dev/null 2> "$tmp_out.log" \
      || { cat "$tmp_out.log" >&2; exit 1; }
    rm -f "$tmp_out.log"
    ;;
  *) echo "cli must be claude or codex" >&2; exit 1 ;;
esac

[[ -s $tmp_out ]] || { echo "review returned no text" >&2; exit 1; }
out=$(mktemp "$authoring_dir/$stem.review-$kind.$cli.$(date -u +%Y%m%dT%H%M%SZ).XXXXXX.md")
{
  echo "<!-- $kind review of $(realpath --relative-to="$repo" "$page") by $cli ($model), $(date -u +%Y-%m-%dT%H:%MZ) -->"
  echo
  cat "$tmp_out"
} > "$out"
echo "$out"

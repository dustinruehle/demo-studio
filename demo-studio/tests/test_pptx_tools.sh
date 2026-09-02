# demo-studio/tests/test_pptx_tools.sh
# Plain assertion script. Exit 0 means every case passed.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../shared/pptx_tools.sh
. "$(dirname "$here")/shared/pptx_tools.sh"

fails=0
ok()   { echo "  ok   - $1"; }
bad()  { echo "  FAIL - $1"; fails=$((fails+1)); }

# 1. find_pptx_skill honours an explicit override
tmp="$(mktemp -d)"; mkdir -p "$tmp/pptx"; touch "$tmp/pptx/SKILL.md"
if [ "$(PPTX_SKILL_DIR="$tmp/pptx" find_pptx_skill)" = "$tmp/pptx" ]; then
  ok "find_pptx_skill honours PPTX_SKILL_DIR"
else
  bad "find_pptx_skill ignored PPTX_SKILL_DIR"
fi

# 2. a bogus override is rejected rather than echoed back
if PPTX_SKILL_DIR="$tmp/nope" find_pptx_skill >/dev/null 2>&1; then
  bad "find_pptx_skill accepted a directory with no SKILL.md"
else
  ok "find_pptx_skill rejects a directory with no SKILL.md"
fi

# 3. failure names every probed location, so the error is actionable
out="$(PPTX_SKILL_DIR="$tmp/nope" find_pptx_skill 2>&1 || true)"
case "$out" in
  *"/mnt/skills/public/pptx"*) ok "failure message names the sandbox path" ;;
  *) bad "failure message did not name the probed locations" ;;
esac

# 4. check_render_tools reports the specific missing tool
out="$(PATH=/nonexistent check_render_tools 2>&1 || true)"
case "$out" in
  *soffice*pdftoppm*|*pdftoppm*soffice*) ok "check_render_tools names both missing tools" ;;
  *) bad "check_render_tools did not name both missing tools: $out" ;;
esac

# 5. preflight emits the exact banner the skill must surface
out="$(PATH=/nonexistent render_preflight 2>&1 || true)"
case "$out" in
  *"VISUAL QA SKIPPED - SLIDES UNVERIFIED"*) ok "render_preflight emits the unverified banner" ;;
  *) bad "render_preflight banner missing" ;;
esac
case "$out" in
  *"brew install --cask libreoffice"*) ok "render_preflight prints the brew command" ;;
  *) bad "render_preflight did not print the brew command" ;;
esac

rm -rf "$tmp"
[ "$fails" -eq 0 ] && echo "PASS" || { echo "$fails failure(s)"; exit 1; }

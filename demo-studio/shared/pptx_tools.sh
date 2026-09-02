# demo-studio/shared/pptx_tools.sh
# Locate the pptx skill and verify the render toolchain. Source this, do not run it.
#
# The skill's visual-QA loop needs the pptx skill's office scripts plus soffice and
# pdftoppm. In the Claude desktop sandbox those live under /mnt; on a developer
# machine they do not. Probe, and fail with something actionable.

# Ordered probe list, for the failure diagnostic. First hit that contains
# SKILL.md wins during resolution (see find_pptx_skill); this full list is
# also what gets printed on failure so the error names every location that
# would normally be checked.
_pptx_candidates() {
  [ -n "${PPTX_SKILL_DIR:-}" ] && printf '%s\n' "$PPTX_SKILL_DIR"
  printf '%s\n' "/mnt/skills/public/pptx"
  printf '%s\n' "$HOME/Library/Application Support/Claude/local-agent-mode-sessions"/*/*/*/skills/pptx
  printf '%s\n' "$HOME/.claude/skills/pptx"
}

find_pptx_skill() {
  local dir
  if [ -n "${PPTX_SKILL_DIR:-}" ]; then
    # An explicit override is authoritative: try only it, so a bad override
    # fails loudly instead of silently falling through to another install
    # that happens to be present on this machine.
    if [ -f "$PPTX_SKILL_DIR/SKILL.md" ]; then
      printf '%s\n' "$PPTX_SKILL_DIR"
      return 0
    fi
  else
    while IFS= read -r dir; do
      [ -n "$dir" ] || continue
      if [ -f "$dir/SKILL.md" ]; then
        printf '%s\n' "$dir"
        return 0
      fi
    done <<EOF
$(_pptx_candidates)
EOF
  fi
  {
    echo "could not locate the pptx skill. Probed:"
    while IFS= read -r dir; do
      [ -n "$dir" ] || continue
      printf '  %s\n' "$dir"
    done <<EOF
$(_pptx_candidates)
EOF
    echo "Set PPTX_SKILL_DIR to override."
  } >&2
  return 1
}

check_render_tools() {
  local missing=""
  command -v soffice   >/dev/null 2>&1 || missing="$missing soffice"
  command -v pdftoppm  >/dev/null 2>&1 || missing="$missing pdftoppm"
  if [ -n "$missing" ]; then
    echo "missing render tools:$missing" >&2
    return 1
  fi
  return 0
}

# Gate for the visual-QA loop. Never installs anything: it reports and returns
# non-zero so the caller decides. The banner is the contract with the skill,
# which must surface it to the user rather than reporting the deck as done.
render_preflight() {
  if check_render_tools 2>/dev/null; then
    return 0
  fi
  local detail
  detail="$(check_render_tools 2>&1 >/dev/null)"
  printf '  %s\n' "$detail" >&2
  printf '%s\n' \
    "" \
    "  To enable the visual-QA loop:" \
    "    brew install --cask libreoffice" \
    "    brew install poppler" \
    "" \
    "  ############################################################" \
    "  #  VISUAL QA SKIPPED - SLIDES UNVERIFIED                   #" \
    "  #  Slides were not rendered or inspected. Do not report    #" \
    "  #  this deck as done. Say plainly that visual QA did not   #" \
    "  #  run and that layout problems would not have been seen.  #" \
    "  ############################################################" >&2
  return 1
}

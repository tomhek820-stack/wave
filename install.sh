#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="https://github.com/tomhek820-stack/wave.git"
BRANCH="${ZORO_VIDEO_BRANCH:-main}"
TARGET_DIR="${ZORO_VIDEO_TARGET:-$PWD}"
FORCE="${ZORO_VIDEO_FORCE:-0}"

log(){ printf '[ZORO VIDEO] %s\n' "$*"; }
die(){ printf '[ZORO VIDEO][ERROR] %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "Git is required. Install Git and retry."
[[ -d "$TARGET_DIR" ]] || die "Target directory does not exist: $TARGET_DIR"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
[[ -w "$TARGET_DIR" ]] || die "Target directory is not writable: $TARGET_DIR"

TMP_DIR="$(mktemp -d)"
cleanup(){ rm -rf "$TMP_DIR"; }
trap cleanup EXIT

log "Cloning $REPO_URL (branch: $BRANCH)"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TMP_DIR/repo" >/dev/null 2>&1 || die "Could not clone repository/branch."
SRC="$TMP_DIR/repo"

for required in CLAUDE.md DIRECTOR_SYSTEM.md WORKFLOW.md QUALITY_CONTROL.md SCENE_SCHEMA.json CLAUDE_WEB_PROMPT.md .claude/skills/video-production/SKILL.md templates/PROJECT_INPUT_TEMPLATE.md; do
  [[ -s "$SRC/$required" ]] || die "Repository package is incomplete: $required"
done

DEST="$TARGET_DIR/.zoro-video-director-pro"
mkdir -p "$DEST"
for file in CLAUDE.md DIRECTOR_SYSTEM.md WORKFLOW.md QUALITY_CONTROL.md SCENE_SCHEMA.json CLAUDE_WEB_PROMPT.md README.md; do
  if [[ -f "$SRC/$file" ]]; then
    if [[ -f "$DEST/$file" && "$FORCE" != "1" ]]; then
      cp "$SRC/$file" "$DEST/$file.new"
      log "Existing managed file preserved; updated candidate saved as $DEST/$file.new"
    else
      cp "$SRC/$file" "$DEST/$file"
    fi
  fi
done

mkdir -p "$TARGET_DIR/.claude/skills/zoro-video-production"
SKILL_DEST="$TARGET_DIR/.claude/skills/zoro-video-production/SKILL.md"
if [[ -f "$SKILL_DEST" && "$FORCE" != "1" ]]; then
  cp "$SRC/.claude/skills/video-production/SKILL.md" "$SKILL_DEST.new"
  log "Existing skill preserved; candidate saved as $SKILL_DEST.new"
else
  cp "$SRC/.claude/skills/video-production/SKILL.md" "$SKILL_DEST"
fi

# Add or safely refresh the managed pointer block without replacing user instructions.
MAIN_CLAUDE="$TARGET_DIR/CLAUDE.md"
BEGIN_MARKER="<!-- ZORO VIDEO DIRECTOR PRO: BEGIN -->"
END_MARKER="<!-- ZORO VIDEO DIRECTOR PRO: END -->"
BLOCK="$BEGIN_MARKER
## ZORO VIDEO DIRECTOR PRO
For video production tasks, follow the installed director system:
- Read `.zoro-video-director-pro/DIRECTOR_SYSTEM.md`
- Read `.zoro-video-director-pro/WORKFLOW.md`
- Read `.zoro-video-director-pro/QUALITY_CONTROL.md`
- Use `.zoro-video-director-pro/SCENE_SCHEMA.json` for scene plans
- Invoke the `zoro-video-production` skill when applicable.
The supplied audio is the timing master. The user provides audio, exact voiceover text, and video content; Claude creates missing scene visuals with tools actually available. Do not require user-provided scene images.
$END_MARKER"

if [[ ! -f "$MAIN_CLAUDE" ]]; then
  printf '%s\n' "$BLOCK" > "$MAIN_CLAUDE"
  log "Created project CLAUDE.md with ZORO instructions."
else
  BEGIN_COUNT="$(grep -Fc "$BEGIN_MARKER" "$MAIN_CLAUDE" || true)"
  END_COUNT="$(grep -Fc "$END_MARKER" "$MAIN_CLAUDE" || true)"
  if [[ "$BEGIN_COUNT" == "0" && "$END_COUNT" == "0" ]]; then
    printf '\n%s\n' "$BLOCK" >> "$MAIN_CLAUDE"
    log "Appended ZORO instructions without replacing existing CLAUDE.md content."
  elif [[ "$BEGIN_COUNT" == "1" && "$END_COUNT" == "1" ]]; then
    TMP_CLAUDE="$TMP_DIR/CLAUDE.md"
    awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
      $0 == begin {
        if (inside || seen_begin) exit 2
        inside=1
        seen_begin=1
        next
      }
      $0 == end {
        if (!inside) exit 2
        inside=0
        seen_end=1
        next
      }
      !inside { print }
      END {
        if (inside || !seen_begin || !seen_end) exit 2
      }
    ' "$MAIN_CLAUDE" > "$TMP_CLAUDE" || die "Malformed ZORO markers in CLAUDE.md; original file was preserved."
    printf '\n%s\n' "$BLOCK" >> "$TMP_CLAUDE"
    cp "$TMP_CLAUDE" "$MAIN_CLAUDE"
    log "Updated the existing managed ZORO instruction block."
  else
    die "Unpaired or duplicated ZORO markers in CLAUDE.md; original file was preserved."
  fi
fi

mkdir -p "$TARGET_DIR/zoro-video-input"
cp "$SRC/templates/PROJECT_INPUT_TEMPLATE.md" "$TARGET_DIR/zoro-video-input/README_INPUT.md"

log "Installation complete."
log "Installed director files: $DEST"
log "Installed Claude Code skill: $SKILL_DEST"
log "Input guide: $TARGET_DIR/zoro-video-input/README_INPUT.md"
log "No existing project files were deleted."
log "To force-refresh managed files, rerun with ZORO_VIDEO_FORCE=1."

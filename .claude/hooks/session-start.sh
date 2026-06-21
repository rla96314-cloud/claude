#!/bin/bash
# SessionStart hook: provision gstack + huashu-design Claude skills and their
# runtime dependencies for Claude Code on the web. Idempotent.
set -euo pipefail

# Only run on remote (Claude Code on the web) sessions; on local installs the
# user manages their own skills.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

log()  { printf "[session-start] %s\n" "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PW_BROWSERS=/opt/pw-browsers

# ── 1. project python deps ─────────────────────────────────────────────
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
  log "pip: installing requirements.txt"
  pip install --quiet --no-input -r "$PROJECT_DIR/requirements.txt" || \
    log "pip install failed (continuing)"
fi

# ── 2. system packages: ffmpeg (huashu video export) + certutil (CA import) ──
APT_NEEDED=()
have ffmpeg  || APT_NEEDED+=(ffmpeg)
have certutil || APT_NEEDED+=(libnss3-tools)
if [ ${#APT_NEEDED[@]} -gt 0 ]; then
  log "apt: installing ${APT_NEEDED[*]}"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${APT_NEEDED[@]}" >/dev/null
fi

# ── 3. egress proxy CAs → Chrome NSS trust store ───────────────────────
# Lets headless Chrome accept HTTPS through the env's TLS-intercepting proxy.
NSSDB="$HOME/.pki/nssdb"
mkdir -p "$NSSDB"
[ -f "$NSSDB/cert9.db" ] || certutil -d "sql:$NSSDB" -N --empty-password
for crt in /usr/local/share/ca-certificates/*.crt; do
  [ -e "$crt" ] || continue
  nick="$(basename "$crt" .crt)"
  if ! certutil -d "sql:$NSSDB" -L -n "$nick" >/dev/null 2>&1; then
    certutil -d "sql:$NSSDB" -A -t "C,," -n "$nick" -i "$crt"
    log "nss: trusted $nick"
  fi
done

# ── 4. Playwright Chrome-for-Testing browsers ──────────────────────────
# cdn.playwright.dev is blocked, but storage.googleapis.com (the CfT origin)
# is allowlisted and serves the identical binaries. Place them at the exact
# revision paths Playwright expects so launch() finds them without download.
#   1208 → gstack's vendored playwright (1.58.2) → Chrome 145.0.7632.6
#   1217 → huashu-design's playwright (1.59.1)  → Chrome 147.0.7727.15
fetch_cft() {
  local rev="$1" chromever="$2"
  local base="https://storage.googleapis.com/chrome-for-testing-public/$chromever/linux64"
  for kind in "chrome-linux64:chromium" "chrome-headless-shell-linux64:chromium_headless_shell"; do
    local zip="${kind%%:*}.zip"
    local dest="$PW_BROWSERS/${kind##*:}-$rev"
    [ -f "$dest/INSTALLATION_COMPLETE" ] && continue
    log "playwright: fetching $zip for rev $rev (Chrome $chromever)"
    mkdir -p "$dest"
    curl -sfL --retry 4 --retry-delay 2 --retry-all-errors --max-time 600 \
      -o "/tmp/$zip" "$base/$zip"
    unzip -q -o "/tmp/$zip" -d "$dest/"
    : > "$dest/INSTALLATION_COMPLETE"
    : > "$dest/DEPENDENCIES_VALIDATED"
    rm -f "/tmp/$zip"
  done
}
mkdir -p "$PW_BROWSERS"
fetch_cft 1208 145.0.7632.6
fetch_cft 1217 147.0.7727.15

# ── 5. gstack skill ────────────────────────────────────────────────────
GSTACK_DIR="$HOME/.claude/skills/gstack"
if [ ! -d "$GSTACK_DIR/.git" ]; then
  log "gstack: cloning"
  git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git "$GSTACK_DIR"
fi
log "gstack: running setup"
(cd "$GSTACK_DIR" && PLAYWRIGHT_BROWSERS_PATH="$PW_BROWSERS" ./setup --quiet)

# ── 6. huashu-design skill ─────────────────────────────────────────────
HUASHU_DIR="$HOME/.claude/skills/huashu-design"
if [ ! -d "$HUASHU_DIR/.git" ]; then
  log "huashu-design: cloning"
  git clone --depth 1 https://github.com/alchaincyf/huashu-design.git "$HUASHU_DIR"
fi
if [ ! -d "$HUASHU_DIR/node_modules" ]; then
  log "huashu-design: npm install"
  (cd "$HUASHU_DIR" && \
   PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
   PLAYWRIGHT_BROWSERS_PATH="$PW_BROWSERS" \
   npm install --no-audit --no-fund --silent)
fi

# ── 7. personal global skills (available in every repo) ───────────────
# Skills under ~/.claude/skills/ are user-global — Claude Code surfaces them
# regardless of which repo the session is in. Repo-scoped skills live under
# <repo>/.claude/skills/ and only apply when that repo is open.
HELLO_DEMO_DIR="$HOME/.claude/skills/hello-demo"
if [ ! -f "$HELLO_DEMO_DIR/SKILL.md" ]; then
  log "hello-demo: installing user-global skill"
  mkdir -p "$HELLO_DEMO_DIR"
  cat > "$HELLO_DEMO_DIR/SKILL.md" <<'SKILL_EOF'
---
name: hello-demo
description: 사용자가 "hello demo"라고 하면 인사하고 현재 시간을 보고하는 데모 스킬.
triggers:
  - hello demo
  - 데모 스킬 테스트
---

## When to invoke this skill

사용자가 "hello demo" 또는 "데모 스킬 테스트"라고 말할 때.

## What to do

1. 한국어로 친근하게 인사한다.
2. 현재 UTC 시각을 `date -u` 로 확인해 보여준다.
3. 이게 사용자 정의 스킬임을 알린다.
SKILL_EOF
fi

# ── 8. expose PLAYWRIGHT_BROWSERS_PATH to the session ─────────────────
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PLAYWRIGHT_BROWSERS_PATH=$PW_BROWSERS" >> "$CLAUDE_ENV_FILE"
fi

log "done"

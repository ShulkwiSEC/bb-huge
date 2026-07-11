#!/usr/bin/env bash
#
# bb-install-tools.sh — installs the recon toolkit bb-huge's methodology
# (bb-recon.md) and automation (app/recon_runner.py, the "Restart Automatic
# Scripts" Danger Zone button) depend on.
#
# Works two ways:
#   1. Inside the bb-huge Docker container:
#        docker compose exec bb-huge bash skills/bb-huge/scripts/bb-install-tools.sh
#   2. Standalone, on your own Debian/Ubuntu/WSL machine (no Docker needed):
#        bash skills/bb-huge/scripts/bb-install-tools.sh
#
# Idempotent — safe to re-run any time to pick up new tools or update
# existing ones. Individual tool failures are logged and skipped, never
# fatal to the rest of the run.
#
# Scope: the core ProjectDiscovery + tomnomnom recon/web toolkit bb-huge's
# own recon pipeline and methodology reference, not the full 350+ curated
# security-skill universe (AD/binary/wifi/cloud tools are a different
# domain entirely and are not installed here).

set -u  # (not -e: a single failed tool must not abort the rest of the run)

GO_VERSION="1.23.4"
GOPATH_DIR="${GOPATH:-$HOME/go}"
# Installed entirely under $HOME deliberately — never needs root/sudo, works
# identically whether this runs as the bbhuge user inside the container
# (docker compose exec bb-huge ...) or as your own user standalone.
GO_INSTALL_DIR="${GO_INSTALL_DIR:-$HOME/.local/go}"

INSTALLED=()
FAILED=()
SKIPPED=()

log()  { printf '[*] %s\n' "$1"; }
warn() { printf '[!] %s\n' "$1" >&2; }

# ── 0. System package prerequisites (best-effort, apt only) ──────────────────

install_apt_prereqs() {
    if ! command -v apt-get >/dev/null 2>&1; then
        warn "apt-get not found — skipping system package install (install git/curl/ca-certificates/build-essential/libpcap-dev yourself if missing)."
        return
    fi
    if [ "$(id -u)" -ne 0 ] && ! command -v sudo >/dev/null 2>&1; then
        warn "Not root and no sudo — skipping apt package install (git/curl/nmap/whatweb/etc)."
        warn "All Go-based tools below install fine without this — they're per-user, no root needed."
        warn "To get nmap/whatweb too: docker compose exec -u root bb-huge apt-get install -y nmap whatweb"
        return
    fi

    local SUDO=""
    [ "$(id -u)" -ne 0 ] && SUDO="sudo"

    log "Installing system prerequisites via apt (git, curl, ca-certificates, unzip, build-essential, libpcap-dev)…"
    $SUDO apt-get update -qq
    $SUDO apt-get install -y --no-install-recommends \
        git curl ca-certificates unzip build-essential libpcap-dev \
        nmap whatweb \
        >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        INSTALLED+=("apt: git/curl/ca-certificates/unzip/build-essential/libpcap-dev/nmap/whatweb")
    else
        warn "Some apt packages failed to install — continuing anyway."
        FAILED+=("apt system packages")
    fi
}

# ── 1. Go toolchain (installed if missing, official binary release) ──────────

ensure_go() {
    if command -v go >/dev/null 2>&1; then
        log "Go already installed: $(go version)"
        return
    fi

    log "Go not found — installing Go ${GO_VERSION}…"
    local arch
    case "$(uname -m)" in
        x86_64)  arch="amd64" ;;
        aarch64|arm64) arch="arm64" ;;
        *) warn "Unsupported architecture $(uname -m) for automatic Go install — install Go manually from https://go.dev/dl/ and re-run this script."; return 1 ;;
    esac

    local tarball="go${GO_VERSION}.linux-${arch}.tar.gz"
    local url="https://go.dev/dl/${tarball}"
    local tmp
    tmp="$(mktemp -d)"

    if ! curl -fsSL "$url" -o "$tmp/$tarball"; then
        warn "Failed to download Go from $url — install manually and re-run."
        rm -rf "$tmp"
        return 1
    fi

    mkdir -p "$(dirname "$GO_INSTALL_DIR")"
    rm -rf "$GO_INSTALL_DIR"
    tar -C "$(dirname "$GO_INSTALL_DIR")" -xzf "$tmp/$tarball"
    rm -rf "$tmp"

    export PATH="$GO_INSTALL_DIR/bin:$PATH"
    if command -v go >/dev/null 2>&1; then
        INSTALLED+=("Go toolchain ${GO_VERSION}")
        log "Go installed: $(go version)"
        log "Add this to your shell profile if running standalone (not needed inside the bb-huge container — see Dockerfile): export PATH=\"$GO_INSTALL_DIR/bin:\$PATH\""
    else
        FAILED+=("Go toolchain")
        warn "Go install did not result in a working 'go' binary."
        return 1
    fi
}

# ── 2. Go-based recon toolkit ─────────────────────────────────────────────────
#
# name|module@version — one go install per line. Add/remove tools here as
# your workflow needs; this list matches bb-recon.md and app/recon_runner.py.

GO_TOOLS='
subfinder|github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
httpx|github.com/projectdiscovery/httpx/cmd/httpx@latest
katana|github.com/projectdiscovery/katana/cmd/katana@latest
dnsx|github.com/projectdiscovery/dnsx/cmd/dnsx@latest
naabu|github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
nuclei|github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
notify|github.com/projectdiscovery/notify/cmd/notify@latest
waybackurls|github.com/tomnomnom/waybackurls@latest
assetfinder|github.com/tomnomnom/assetfinder@latest
gf|github.com/tomnomnom/gf@latest
anew|github.com/tomnomnom/anew@latest
unfurl|github.com/tomnomnom/unfurl@latest
qsreplace|github.com/tomnomnom/qsreplace@latest
gau|github.com/lc/gau/v2/cmd/gau@latest
ffuf|github.com/ffuf/ffuf/v2@latest
amass|github.com/owasp-amass/amass/v4/...@master
'

install_go_tools() {
    if ! command -v go >/dev/null 2>&1; then
        warn "Go unavailable — skipping all Go-based tools."
        return
    fi

    log "GOPATH: $GOPATH_DIR (binaries land in $GOPATH_DIR/bin)"

    while IFS='|' read -r name module; do
        [ -z "$name" ] && continue
        if command -v "$name" >/dev/null 2>&1; then
            log "$name already installed — updating to latest."
        fi
        printf '[*] Installing %-14s ' "$name"
        if GOFLAGS="-mod=mod" go install -v "$module" >/tmp/bb-install-tools-"$name".log 2>&1; then
            echo "OK"
            INSTALLED+=("$name")
        else
            echo "FAILED (see /tmp/bb-install-tools-$name.log)"
            FAILED+=("$name")
        fi
    done <<< "$GO_TOOLS"
}

# ── 3. gf patterns (bonus — gf is useless without them) ───────────────────────

install_gf_patterns() {
    if ! command -v gf >/dev/null 2>&1; then
        return
    fi
    if [ -d "$HOME/.gf" ] && [ -n "$(ls -A "$HOME/.gf" 2>/dev/null)" ]; then
        log "gf patterns already present in $HOME/.gf"
        return
    fi
    log "Fetching gf patterns…"
    local tmp
    tmp="$(mktemp -d)"
    if git clone --depth 1 https://github.com/1ndianl33t/Gf-Patterns "$tmp/Gf-Patterns" >/dev/null 2>&1; then
        mkdir -p "$HOME/.gf"
        cp "$tmp/Gf-Patterns"/*.json "$HOME/.gf/" 2>/dev/null
        INSTALLED+=("gf patterns")
    else
        FAILED+=("gf patterns")
    fi
    rm -rf "$tmp"
}

# ── Run ────────────────────────────────────────────────────────────────────────

main() {
    log "bb-huge recon toolkit installer starting…"
    install_apt_prereqs
    ensure_go
    install_go_tools
    install_gf_patterns

    echo
    echo "══════════════════════════════════════════════════════════"
    echo " bb-huge tool install summary"
    echo "══════════════════════════════════════════════════════════"
    [ ${#INSTALLED[@]} -gt 0 ] && printf ' OK      %s\n' "${INSTALLED[@]}"
    [ ${#FAILED[@]}    -gt 0 ] && printf ' FAILED  %s\n' "${FAILED[@]}"
    [ ${#SKIPPED[@]}   -gt 0 ] && printf ' SKIPPED %s\n' "${SKIPPED[@]}"
    echo "══════════════════════════════════════════════════════════"
    if [ ${#FAILED[@]} -gt 0 ]; then
        echo " Some tools failed — re-run this script any time, it's idempotent."
        exit 1
    fi
    echo " Done. If running standalone (not in the bb-huge container),"
    echo " make sure \$GOPATH/bin ($GOPATH_DIR/bin) is on your PATH."
}

main

#!/bin/sh
# Installs every agent the benchmark compares, at the versions RESULTS.md
# reports, into the benchmark's own locations. run.py uses these installs
# before anything on your PATH, so a global upgrade can't change a run.
#
#   ./install-agents.sh            # everything
#   ./install-agents.sh npm        # or just one group: npm, uv, bin
#
# Needs npm, uv, curl and tar (plus unzip on macOS). Chanto itself comes from a
# sibling checkout (../chanto, `cargo build --release`), not from here.
set -eu

PREFIX=${BENCH_HOME:-$HOME/.local/share/chanto-bench}
HERE=$(cd "$(dirname "$0")" && pwd)
only=${1:-all}

need() { command -v "$1" >/dev/null 2>&1 || { echo "error: $1 is required" >&2; exit 1; }; }
sha256() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }

# Downloads $1 to $2 and checks it against the SHA-256 in $3.
fetch() {
    curl -fsSL -o "$2" "$1"
    got=$(sha256 "$2")
    if [ "$got" != "$3" ]; then
        echo "error: $1 has SHA-256 $got, expected $3" >&2
        rm -f "$2"
        exit 1
    fi
}

# npm agents, from agents/package-lock.json (every dependency pinned):
# Claude Code, Codex, Cline, Continue, Crush, Forge, Kilo Code, Pi, Qwen Code.
install_npm() {
    need npm
    mkdir -p "$PREFIX/agents"
    cp "$HERE/agents/package.json" "$HERE/agents/package-lock.json" "$PREFIX/agents/"
    (cd "$PREFIX/agents" && npm ci --no-audit --no-fund)
}

# Python agents, as uv tools (~/.local/share/uv/tools).
install_uv() {
    need uv
    uv tool install --force aider-chat==0.86.2
    uv tool install --force openhands==1.16.0
}

# Standalone binaries: Goose 1.54.0 (GitHub release) and opencode 2.0.22 (its
# official builds, checksums from the opencode Homebrew formula for 2.0.22).
install_bin() {
    need curl
    need tar
    os=$(uname -s)
    arch=$(uname -m)
    case "$os/$arch" in
        Darwin/arm64)
            goose="goose-aarch64-apple-darwin.tar.gz"
            goose_sha="feda29744cd4e13f9a5211a968ed47c67fb8fa79647f4d271d92d564998a393c"
            oc="opencode-darwin-arm64.zip"
            oc_sha="b152ebd6ae63790e1f4751494d9db35266e7d06118e3a79afb4f65d549441db6" ;;
        Darwin/x86_64)
            goose="goose-x86_64-apple-darwin.tar.gz"
            goose_sha="7cf5bcd0c23983993900a4da49c91a0eb30ad492d2ff85af3e03bb718fb9b8af"
            oc="opencode-darwin-x64-baseline.zip"
            oc_sha="209d2996c45583cf64634d2ebc1aa4bdf665432cd6506c45a65964b2aa2d3013" ;;
        Linux/aarch64 | Linux/arm64)
            goose="goose-aarch64-unknown-linux-gnu.tar.gz"
            goose_sha="0f174b5118a53888cd4e65b7ca9a4b72dd0b887e89142c8ce41e2409205e40d5"
            oc="opencode-linux-arm64.tar.gz"
            oc_sha="3f4df7efe28a53830777666e160984cf8247938e68f105b8ae1f9b4778febc2d" ;;
        Linux/x86_64)
            goose="goose-x86_64-unknown-linux-gnu.tar.gz"
            goose_sha="ab396c95aebbd28b4d38c175234be8d4a3ea0c96e7ccb24c307e4618c9be57e1"
            oc="opencode-linux-x64-baseline.tar.gz"
            oc_sha="6414bc6a441ef28bc549984baf2f60fb95e8fe46713bd17293921400ddfe6d33" ;;
        *)
            echo "error: no pinned Goose or opencode build for $os/$arch" >&2
            exit 1 ;;
    esac
    dl="$PREFIX/downloads"
    mkdir -p "$dl" "$PREFIX/bin"

    fetch "https://github.com/block/goose/releases/download/v1.54.0/$goose" "$dl/$goose" "$goose_sha"
    tar -xzf "$dl/$goose" -C "$PREFIX/bin" ./goose

    fetch "https://opencode.ai/files/bin/2.0.22/$oc" "$dl/$oc" "$oc_sha"
    case "$oc" in
        *.zip) need unzip; unzip -o -q "$dl/$oc" opencode -d "$PREFIX/bin" ;;
        *) tar -xzf "$dl/$oc" -C "$PREFIX/bin" opencode ;;
    esac
    chmod +x "$PREFIX/bin/goose" "$PREFIX/bin/opencode"
}

case "$only" in
    all) install_npm; install_uv; install_bin ;;
    npm) install_npm ;;
    uv) install_uv ;;
    bin) install_bin ;;
    *) echo "usage: $0 [npm|uv|bin]" >&2; exit 2 ;;
esac

echo "Installed into $PREFIX (uv tools in ~/.local/share/uv/tools)."
echo "Check what a run will use: python3 run.py --estimate --agents <names>"

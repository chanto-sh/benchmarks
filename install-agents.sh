#!/bin/sh
# Installs every agent the benchmark compares, at the versions RESULTS.md
# reports, into the benchmark's own locations. run.py uses these installs
# before anything on your PATH, so a global upgrade can't change a run.
#
#   ./install-agents.sh            # everything
#   ./install-agents.sh npm        # or just one group: npm, uv, bin
#   ./install-agents.sh hax        # or one binary agent: chanto, goose,
#                                  # opencode, codewhale, zerostack, hax
#
# Needs npm, uv, curl and tar (plus unzip on macOS). `./install-agents.sh chanto`
# installs the pinned Chanto release, which reproduce.py measures; run.py
# otherwise uses a sibling checkout's build (../chanto, `cargo build --release`).
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
# Claude Code, Codex, Cline, Continue, Crush, Forge, Gemini CLI, Kilo Code, Pi,
# Qwen Code.
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

# Standalone binaries, each a GitHub release (or official build) checked
# against a pinned SHA-256:
#   Chanto 0.1.4 (checksums from the release's signed SHA256SUMS);
#   Goose 1.54.0;
#   opencode 2.0.22 (checksums from the opencode Homebrew formula for 2.0.22);
#   Codewhale 0.10.1, zerostack 1.8.5, hax 0.6.1 (checksums
#   cross-checked against each release's own SHA-256 manifest).
platform() {
    case "$(uname -s)/$(uname -m)" in
        Darwin/arm64) echo darwin-arm64 ;;
        Darwin/x86_64) echo darwin-x64 ;;
        Linux/aarch64 | Linux/arm64) echo linux-arm64 ;;
        Linux/x86_64) echo linux-x64 ;;
        *) echo "error: no pinned binaries for $(uname -s)/$(uname -m)" >&2; exit 1 ;;
    esac
}

bin_setup() {
    need curl
    need tar
    plat=$(platform)
    dl="$PREFIX/downloads"
    mkdir -p "$dl" "$PREFIX/bin"
}

CHANTO_VERSION=0.1.4

install_chanto() {
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=480c309cfbdd9384a7f7291fa36cc06cbdd30257480dd7faa92ad81c3e85ebee ;;
        darwin-x64) t=x86_64-apple-darwin; sha=c79efb1baa8fbf442f8888ecdcaca370733901ec7ac108ebbab5df5a484ec9ac ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=5e48c352555fc24e12e13643781b41b9e5aa1e628c2cc6d9311db168310419eb ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=d55ff2670b5afb3a3b5c665bd819458d63cf79a77efcfbfd559fee2d61166145 ;;
    esac
    f=chanto-v$CHANTO_VERSION-$t.tar.gz
    fetch "https://github.com/chanto-sh/chanto/releases/download/v$CHANTO_VERSION/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$dl" "chanto-v$CHANTO_VERSION-$t/chanto"
    rm -f "$PREFIX/bin/chanto"
    cat "$dl/chanto-v$CHANTO_VERSION-$t/chanto" > "$PREFIX/bin/chanto"
    rm -rf "$dl/$f" "$dl/chanto-v$CHANTO_VERSION-$t"
    chmod +x "$PREFIX/bin/chanto"
}

install_goose() {
    case "$plat" in
        darwin-arm64) f=goose-aarch64-apple-darwin.tar.gz; sha=feda29744cd4e13f9a5211a968ed47c67fb8fa79647f4d271d92d564998a393c ;;
        darwin-x64) f=goose-x86_64-apple-darwin.tar.gz; sha=7cf5bcd0c23983993900a4da49c91a0eb30ad492d2ff85af3e03bb718fb9b8af ;;
        linux-arm64) f=goose-aarch64-unknown-linux-gnu.tar.gz; sha=0f174b5118a53888cd4e65b7ca9a4b72dd0b887e89142c8ce41e2409205e40d5 ;;
        linux-x64) f=goose-x86_64-unknown-linux-gnu.tar.gz; sha=ab396c95aebbd28b4d38c175234be8d4a3ea0c96e7ccb24c307e4618c9be57e1 ;;
    esac
    fetch "https://github.com/block/goose/releases/download/v1.54.0/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$PREFIX/bin" ./goose
    chmod +x "$PREFIX/bin/goose"
}

install_opencode() {
    case "$plat" in
        darwin-arm64) f=opencode-darwin-arm64.zip; sha=b152ebd6ae63790e1f4751494d9db35266e7d06118e3a79afb4f65d549441db6 ;;
        darwin-x64) f=opencode-darwin-x64-baseline.zip; sha=209d2996c45583cf64634d2ebc1aa4bdf665432cd6506c45a65964b2aa2d3013 ;;
        linux-arm64) f=opencode-linux-arm64.tar.gz; sha=3f4df7efe28a53830777666e160984cf8247938e68f105b8ae1f9b4778febc2d ;;
        linux-x64) f=opencode-linux-x64-baseline.tar.gz; sha=6414bc6a441ef28bc549984baf2f60fb95e8fe46713bd17293921400ddfe6d33 ;;
    esac
    fetch "https://opencode.ai/files/bin/2.0.22/$f" "$dl/$f" "$sha"
    case "$f" in
        *.zip) need unzip; unzip -o -q "$dl/$f" opencode -d "$PREFIX/bin" ;;
        *) tar -xzf "$dl/$f" -C "$PREFIX/bin" opencode ;;
    esac
    chmod +x "$PREFIX/bin/opencode"
}

# A bare executable, not an archive (the release's `codew` is the same file).
# Copied out of the download rather than kept where curl wrote it: on APFS a
# streamed download can hold ~15% more disk than its size, which size.py
# would count.
install_codewhale() {
    case "$plat" in
        darwin-arm64) f=codewhale-macos-arm64; sha=e50fdb7dfbb39d7c01eb63175da01bc40f16fb958e01cbcbef03220460302654 ;;
        darwin-x64) f=codewhale-macos-x64; sha=67019fd263cf6b1c8608e1748e368d472346da0ad417ef5b9428a887dfbb9cb1 ;;
        linux-arm64) f=codewhale-linux-arm64; sha=efe702a5083fe78a7e09676b129dedba4f595a12b4c824c7f1a794da9ca6d6da ;;
        linux-x64) f=codewhale-linux-x64; sha=ed2d83b3853de803ee39f574c745d1e1c9f6f8bf99ed3aec3835425e0c26993b ;;
    esac
    fetch "https://github.com/codewhale-hq/Codewhale/releases/download/v0.10.1/$f" "$dl/$f" "$sha"
    rm -f "$PREFIX/bin/codewhale"
    cat "$dl/$f" > "$PREFIX/bin/codewhale"
    rm -f "$dl/$f"
    chmod +x "$PREFIX/bin/codewhale"
}

# The standard build (the release also has a smaller `zerostack-lite`).
install_zerostack() {
    case "$plat" in
        darwin-arm64) f=zerostack-aarch64-apple-darwin.tar.gz; sha=c327c4015bb7469ab96519a1377a26f50529c2ec3d6a7d11aa512c40770d29b0 ;;
        darwin-x64) f=zerostack-x86_64-apple-darwin.tar.gz; sha=09493ff6f1f274fe89f2371e80f6878ae4d87fdc19d37b3ab7978a9c2611bac7 ;;
        linux-arm64) f=zerostack-aarch64-unknown-linux-gnu.tar.gz; sha=a46b8637fa9445063bbeafcb341172660157fbe96c29847de12bffa5b3b68524 ;;
        linux-x64) f=zerostack-x86_64-unknown-linux-gnu.tar.gz; sha=e8503e6dfc62a8d20aae269427987f3c164d65c023e7b070371b80344cfa89eb ;;
    esac
    fetch "https://github.com/gi-dellav/zerostack/releases/download/v1.8.5/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$PREFIX/bin" zerostack
    rm -f "$dl/$f"
    chmod +x "$PREFIX/bin/zerostack"
}

install_hax() {
    case "$plat" in
        darwin-arm64) f=hax-0.6.1-macos-arm64.tar.gz; sha=e8e317abe4ed565db9aff2f0faeb409d3edf7721adb850e66ae335aea8b280d2 ;;
        linux-arm64) f=hax-0.6.1-linux-aarch64.tar.gz; sha=77e116bba4c9e46d63987958c4be095e1f3b0779391aad539d72504bea3a2e05 ;;
        linux-x64) f=hax-0.6.1-linux-x86_64.tar.gz; sha=d648c6542014fbbb8d4789e5ad9723f213fb61f259815e54d51fd1dcd19b9ec9 ;;
        *) echo "warning: hax 0.6.1 has no $plat build; skipping it" >&2; return 0 ;;
    esac
    fetch "https://github.com/OleksandrChekhovskyi/hax/releases/download/v0.6.1/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$PREFIX/bin" hax
    rm -f "$dl/$f"
    chmod +x "$PREFIX/bin/hax"
}

bin_agents="chanto goose opencode codewhale zerostack hax"

install_bin() {
    bin_setup
    for a in $bin_agents; do "install_$a"; done
}

case "$only" in
    all) install_npm; install_uv; install_bin ;;
    npm) install_npm ;;
    uv) install_uv ;;
    bin) install_bin ;;
    *)
        # One binary agent by name, e.g. `./install-agents.sh hax`.
        case " $bin_agents " in
            *" $only "*) bin_setup; "install_$only" ;;
            *) echo "usage: $0 [npm|uv|bin|<binary agent>]" >&2; exit 2 ;;
        esac ;;
esac

echo "Installed into $PREFIX (uv tools in ~/.local/share/uv/tools)."
echo "Check what a run will use: python3 run.py --estimate --agents <names>"

#!/bin/sh
# Installs every agent the benchmark compares, at the versions RESULTS.md
# reports, into the benchmark's own locations. run.py uses these installs
# before anything on your PATH, so a global upgrade can't change a run.
#
#   ./install-agents.sh            # everything
#   ./install-agents.sh npm        # or just one group: npm, uv, bin
#   ./install-agents.sh hax        # or one binary agent: chanto, goose,
#                                  # opencode, codewhale, zerostack, hax,
#                                  # jcode, reasonix, omp, interpreter, grok, fx
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

# Python agents, as uv tools (~/.local/share/uv/tools). All run on Python
# 3.12, which uv downloads if needed; left to choose, uv takes the newest
# interpreter it finds, and on a machine with a newer Python than the agents'
# compiled dependencies support (macos-latest ships 3.15) the install fails
# building them from source.
install_uv() {
    need uv
    uv tool install --force --python 3.12 aider-chat==0.86.2
    uv tool install --force --python 3.12 openhands==1.16.0
    # mini-swe-agent's litellm stays at the release the proxy pins (1.106.2):
    # 1.107.0 shipped a credential stealer, and later ones aren't vetted here.
    uv tool install --force --python 3.12 mini-swe-agent==2.4.6 --with litellm==1.106.2
    uv tool install --force --python 3.12 mistral-vibe==3.0.3
}

# Standalone binaries, each a GitHub release (or official build) checked
# against a pinned SHA-256:
#   Chanto 0.1.10 (checksums from the release's signed SHA256SUMS);
#   Goose 1.54.0;
#   opencode 2.0.22 (checksums from the opencode Homebrew formula for 2.0.22);
#   jcode 0.99.1, DeepSeek-Reasonix 2.54.0, oh-my-pi 18.13.3, Open Interpreter 0.0.56,
#   fx 0.0.15 (checksums from each GitHub release's own SHA-256 digests);
#   Grok Build 1.0.70 (see install_grok);
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

CHANTO_VERSION=0.1.10

install_chanto() {
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=32b28b0b92f004a56b0710eb4bac6603d2d00f4a18e88b16881d3a9be225ead9 ;;
        darwin-x64) t=x86_64-apple-darwin; sha=2d120b949a53f7d0c02d1268030c6ac8c872f2515a8039d7879bd29257dd31b0 ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=76e86507f1ff23ff6363f930864cd5bfa4289dc844283749e975d890e2ffded5 ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=6cac3c5712abd78473824abd433ba09f999b237974bca9d38f2e3d671505c20a ;;
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

install_jcode() {
    case "$plat" in
        darwin-arm64) f=jcode-macos-aarch64.tar.gz; sha=3623164d518b0c9d443ab07052084244b379e8a3377037db67d2382220f4ed14 ;;
        darwin-x64) f=jcode-macos-x86_64.tar.gz; sha=d7d53c40b1e105926e06df5aa02c0f082616d602bbd20e0c318248ce3fdad4c9 ;;
        linux-arm64) f=jcode-linux-aarch64.tar.gz; sha=f66ffbaf7c4c0124f45d6c8616571146deb8509b8beef2e8c0d76cc35dda9b91 ;;
        linux-x64) f=jcode-linux-x86_64.tar.gz; sha=0b2a612de97c6e01ae6de1c0cff555b3460cf8364d1a11d2f8649fc0c9d7a1e6 ;;
    esac
    fetch "https://github.com/1jehuang/jcode/releases/download/v0.99.1/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/jcode" && tar -xzf "$dl/$f" -C "$dl/jcode"
    # On Linux the plain name is a launcher script for the .bin next to it (it
    # only adds its own folder to LD_LIBRARY_PATH; the archive has no libraries).
    src="$dl/jcode/$(basename "$f" .tar.gz)"
    [ -f "$src.bin" ] && src="$src.bin"
    rm -f "$PREFIX/bin/jcode"
    cat "$src" > "$PREFIX/bin/jcode"
    rm -rf "$dl/$f" "$dl/jcode"
    chmod +x "$PREFIX/bin/jcode"
}

install_reasonix() {
    case "$plat" in
        darwin-arm64) f=reasonix-darwin-arm64.tar.gz; sha=be4e185703c1a3f95f140bbb785ce4861d5008689916fe892ed2683424a9fe10 ;;
        darwin-x64) f=reasonix-darwin-amd64.tar.gz; sha=6b5d36a6564e818452fe28f291816dde458319c3f4ab7409e91074f234a66a3e ;;
        linux-arm64) f=reasonix-linux-arm64.tar.gz; sha=05ed53becb3cd2bb91f961065690b6c90d0af8e10e7279e8bed4a499441d8397 ;;
        linux-x64) f=reasonix-linux-amd64.tar.gz; sha=52b834fbbf2c05d69efad8b88366d535df31cbe3433c1f0d65fe939180220c3d ;;
    esac
    fetch "https://github.com/esengine/DeepSeek-Reasonix/releases/download/studio-v2.54.0/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/reasonix" && tar -xzf "$dl/$f" -C "$dl/reasonix" reasonix
    rm -f "$PREFIX/bin/reasonix"
    cat "$dl/reasonix/reasonix" > "$PREFIX/bin/reasonix"
    rm -rf "$dl/$f" "$dl/reasonix"
    chmod +x "$PREFIX/bin/reasonix"
}

# oh-my-pi ships bare executables (a Bun single-file build).
install_omp() {
    case "$plat" in
        darwin-arm64) f=omp-darwin-arm64; sha=b449d0d0d779a0b2e655f0ce41d5c414a253de71c67b3affc30a6528fc967314 ;;
        darwin-x64) f=omp-darwin-x64; sha=cfd47dc46d028bbdfc220ccb1fdd40af7a82a4e182cb3c2fd1d66a8c20d90326 ;;
        linux-arm64) f=omp-linux-arm64; sha=981f08df6c6344356b31aa696fdd810b8b5fa8c8851ba926d3940e793d47cc3a ;;
        linux-x64) f=omp-linux-x64; sha=42d39fa8996fed9f999e26306e60e2fdbea0c0de0d0b2d68feba275f44c41d04 ;;
    esac
    fetch "https://github.com/can1357/oh-my-pi/releases/download/v18.13.3/$f" "$dl/$f" "$sha"
    rm -f "$PREFIX/bin/omp"
    cat "$dl/$f" > "$PREFIX/bin/omp"
    rm -f "$dl/$f"
    chmod +x "$PREFIX/bin/omp"
}

# Open Interpreter is a Codex fork and keeps Codex's asset names.
install_interpreter() {
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=837570739cf7cd13e0d5b88cc18d6aea33e31eba3682844218fdb050640deee2 ;;
        darwin-x64) t=x86_64-apple-darwin; sha=9f998b2b61c60e60e3c5e8d6006bdda44884175c19ac518eccc0f5d8a7a10689 ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=a3bb3e37cd4a29f35bbd0021c4fbebec5a858a159edb1c09775f209becb53810 ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=c0f76523f8585a3bd8985638bf8861d70ab86fb9e9b02c6bf96a54680458fe0b ;;
    esac
    f=codex-$t.tar.gz
    fetch "https://github.com/openinterpreter/openinterpreter/releases/download/rust-v0.0.56/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/interpreter" && tar -xzf "$dl/$f" -C "$dl/interpreter"
    rm -f "$PREFIX/bin/interpreter"
    cat "$dl/interpreter/codex-$t" > "$PREFIX/bin/interpreter"
    rm -rf "$dl/$f" "$dl/interpreter"
    chmod +x "$PREFIX/bin/interpreter"
}

# fx ships a tarball per platform with its own .sha256 next to it.
install_fx() {
    case "$plat" in
        darwin-arm64) f=fx-macos-aarch64.tar.gz; sha=9f7dcae1f42080d8a668ff8fec172d90d071a52540255776479bf973bc5a349b ;;
        darwin-x64) f=fx-macos-x86_64.tar.gz; sha=dfa5199908150c19a9c8adc90f72bccefbe17d6740eddd0240f3b943ccdaf610 ;;
        linux-arm64) f=fx-linux-aarch64.tar.gz; sha=1c06e770aa87e39c6a4807d6a42fc5508d051e4a381fb2c35e0728fc1f41d461 ;;
        linux-x64) f=fx-linux-x86_64.tar.gz; sha=52def957321dc482c635ed613a4fff3489202b0374b6ccc6dc823e65736bbf26 ;;
    esac
    fetch "https://github.com/vercel-labs/fx/releases/download/v0.0.15/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/fx" && tar -xzf "$dl/$f" -C "$dl/fx" fx
    rm -f "$PREFIX/bin/fx"
    cat "$dl/fx/fx" > "$PREFIX/bin/fx"
    rm -rf "$dl/$f" "$dl/fx"
    chmod +x "$PREFIX/bin/fx"
}

# Grok Build ships bare executables from x.ai with no published checksums (its
# own installer checks none). These were pinned when the same bytes came from
# both of its origins, x.ai and its Google Cloud Storage bucket; the macOS
# build is also signed by xAI (team 5Y6N3AJ54S).
install_grok() {
    case "$plat" in
        darwin-arm64) p=macos-aarch64; sha=5c8a688251bf61e35370b828b6a353b0a20fcc3f64000de8a91d426039f29cec ;;
        darwin-x64) p=macos-x86_64; sha=d9ecd462f1f3c3b40a7a131944987ee7ed1c38069b7009cc4107398ab767f484 ;;
        linux-arm64) p=linux-aarch64; sha=3aa36883574b263088e5addffe241f55430e8daaee1a0c4934b02180007a9761 ;;
        linux-x64) p=linux-x86_64; sha=22d281c5964c5444147328096ba2a221f3f0874c6858e27c825656a80f6e58e9 ;;
    esac
    fetch "https://x.ai/cli/grok-1.0.70-$p" "$dl/grok" "$sha"
    rm -f "$PREFIX/bin/grok"
    cat "$dl/grok" > "$PREFIX/bin/grok"
    rm -f "$dl/grok"
    chmod +x "$PREFIX/bin/grok"
}

bin_agents="chanto goose opencode codewhale zerostack hax jcode reasonix omp interpreter grok fx"

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

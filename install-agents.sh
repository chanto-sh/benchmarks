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
    # mini-swe-agent's litellm moves with the rest, but never to a release in
    # update_agents.py's BLOCKED (1.107.0 shipped a credential stealer).
    uv tool install --force --python 3.12 mini-swe-agent==2.4.6 --with litellm==1.109.1
    uv tool install --force --python 3.12 mistral-vibe==3.1.2
}

# Standalone binaries, each pinned by version and SHA-256:
#   Chanto 0.1.20 (checksums from the release's signed SHA256SUMS);
#   the rest move to their latest releases through update_agents.py: GitHub
#   ones with each file's checksum from GitHub's own SHA-256 digest (opencode
#   too, from its GitHub releases), and Grok Build when x.ai and its Cloud
#   Storage bucket serve the same bytes.
# On Windows (win32-x64) each agent's .exe comes through win_install, pinned
# the same way.
platform() {
    case "$(uname -s)/$(uname -m)" in
        Darwin/arm64) echo darwin-arm64 ;;
        Darwin/x86_64) echo darwin-x64 ;;
        Linux/aarch64 | Linux/arm64) echo linux-arm64 ;;
        Linux/x86_64) echo linux-x64 ;;
        # Git Bash on Windows (the reproduce workflow's Windows runner).
        MINGW*/x86_64 | MSYS*/x86_64) echo win32-x64 ;;
        *) echo "error: no pinned binaries for $(uname -s)/$(uname -m)" >&2; exit 1 ;;
    esac
}

bin_setup() {
    need curl
    need tar
    plat=$(platform)
    # Windows Python is `python`; `python3` there can be a Store placeholder.
    py=python3
    [ "$plat" = win32-x64 ] && py=python
    dl="$PREFIX/downloads"
    mkdir -p "$dl" "$PREFIX/bin"
}

CHANTO_VERSION=0.1.20

install_chanto() {
    [ "$plat" = win32-x64 ] && { win_install chanto "https://github.com/chanto-sh/chanto/releases/download/v$CHANTO_VERSION/chanto-v$CHANTO_VERSION-x86_64-pc-windows-msvc.zip" eb3868da159e42df85bb22c97523873da6d9a1d71bb41cce83d141b53f7ebd6b chanto.exe; return; }
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=5d7ff9e8d3efebb4a640d4e4455dfc94556c7f44e8371e4607d8e977d71dc81c ;;
        darwin-x64) t=x86_64-apple-darwin; sha=68c0acf5e9ebcfc11706d3f2e30987cda8a35bd3c61d45a42bca80000ff8b172 ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=5fb3c3d0881a838fd1125b3076cb4b6e75b0bbd3e36edfc9a3e55f0fdfcc2d7b ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=191a4042ed671f63da91d2fe6d0396a75b2bde95d0bb9ca8922cfc4374bcc12d ;;
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
    [ "$plat" = win32-x64 ] && { win_install goose https://github.com/block/goose/releases/download/v1.59.0/goose-x86_64-pc-windows-msvc.zip 8b9ef7be66f469bdafd018de943a095ed83c32775dd623bebb0ab730da22d0d0 goose.exe; return; }
    case "$plat" in
        darwin-arm64) f=goose-aarch64-apple-darwin.tar.gz; sha=0142839f339e3484b49326d69de9d9cf808999087ab421ae9304d2620e647cbc ;;
        darwin-x64) f=goose-x86_64-apple-darwin.tar.gz; sha=1a15f649cabbdeccbb1905483a6c30681375653264273f022e03358ba53ad2ce ;;
        linux-arm64) f=goose-aarch64-unknown-linux-gnu.tar.gz; sha=ba96b78394e3050077482bb285ff35f34613646e90b84a18b5d674b71905166e ;;
        linux-x64) f=goose-x86_64-unknown-linux-gnu.tar.gz; sha=a774667de6c20206a60d78d7bece2d9dda8389667e4f5c2fc8aaa758d1e81ef3 ;;
    esac
    fetch "https://github.com/block/goose/releases/download/v1.59.0/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$PREFIX/bin" ./goose
    chmod +x "$PREFIX/bin/goose"
}

install_opencode() {
    [ "$plat" = win32-x64 ] && { win_install opencode https://github.com/sst/opencode/releases/download/v2.2.7/opencode-windows-x64-baseline.zip 93323d0d6f72f9d1ba9f847e8002de71ace79bb5ea64f18d6b70bbbc30cc719e opencode.exe; return; }
    case "$plat" in
        darwin-arm64) f=opencode-darwin-arm64.zip; sha=811c42be9cad489ea8c411ead49e06f691deee4957ba9a0a56a159a7d6c1abdc ;;
        darwin-x64) f=opencode-darwin-x64-baseline.zip; sha=7830c9ce3945ad9fee792f603d4c9abcbb041b5cabafb51ce3c40da1dad5b435 ;;
        linux-arm64) f=opencode-linux-arm64.tar.gz; sha=c1682057f0815cb2abdd6e00305f1146ebaf1c167f0335cdb74ddc80008120e7 ;;
        linux-x64) f=opencode-linux-x64-baseline.tar.gz; sha=89a6cee227b54bc011179c528a5e63176032462b1a5e21723b616801cddc2ca7 ;;
    esac
    fetch "https://github.com/sst/opencode/releases/download/v2.2.7/$f" "$dl/$f" "$sha"
    case "$f" in
        *.zip) need unzip; unzip -o -q "$dl/$f" opencode -d "$PREFIX/bin" ;;
        *) tar -xzf "$dl/$f" -C "$PREFIX/bin" opencode ;;
    esac
    chmod +x "$PREFIX/bin/opencode"
}

# Windows: agent $1's .exe from $2, checked against SHA-256 $3. The download is
# either the .exe itself or a zip holding it as $4 (found wherever it sits;
# Git Bash's tar can't read zips).
win_install() {
    f=${2##*/}
    fetch "$2" "$dl/$f" "$3"
    case "$f" in
        *.exe) cat "$dl/$f" > "$PREFIX/bin/$1.exe" ;;
        *) "$py" - "$dl/$f" "$4" "$PREFIX/bin/$1.exe" <<'PY'
import shutil, sys, zipfile
archive, member, out = sys.argv[1:]
with zipfile.ZipFile(archive) as z:
    names = [n for n in z.namelist() if n.rsplit("/", 1)[-1] == member]
    if not names:
        sys.exit(f"error: {archive} has no {member}")
    with z.open(names[0]) as src, open(out, "wb") as dst:
        shutil.copyfileobj(src, dst)
PY
            ;;
    esac
    rm -f "$dl/$f"
}

# A bare executable, not an archive (the release's `codew` is the same file).
# Copied out of the download rather than kept where curl wrote it: on APFS a
# streamed download can hold ~15% more disk than its size, which size.py
# would count.
install_codewhale() {
    [ "$plat" = win32-x64 ] && { win_install codewhale https://github.com/codewhale-hq/Codewhale/releases/download/v0.10.2/codewhale-windows-x64.exe 578280bec8d6e0ee9cfe97ee29de817535689f4078d8afd47384ff1941b1ee6c; return; }
    case "$plat" in
        darwin-arm64) f=codewhale-macos-arm64; sha=da0229610647f1cc2dd14c4227b333a92ea276a49f5d4d79160fa19e515e590d ;;
        darwin-x64) f=codewhale-macos-x64; sha=ac135d8961525b4092101a15874016d42f71ef821c9c34db3b8f936aad9cb988 ;;
        linux-arm64) f=codewhale-linux-arm64; sha=b7c55e36f7ef30c8fae4b8741bfaf9e0177220a9d4d6d3e26650609b4d9ffe90 ;;
        linux-x64) f=codewhale-linux-x64; sha=28ac984a2f145bf99b29933498a3f951a591283c22782933ce933861dda6c70b ;;
    esac
    fetch "https://github.com/codewhale-hq/Codewhale/releases/download/v0.10.2/$f" "$dl/$f" "$sha"
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
        darwin-arm64) f=hax-0.7.0-macos-arm64.tar.gz; sha=98ae064d6d518992df0ad01eba1315bfaab8a7e3245cd5e312aa49b979159cc9 ;;
        linux-arm64) f=hax-0.7.0-linux-aarch64.tar.gz; sha=57714f4ac1df31232e3e77bea97ccd6c9149ea19a3ea69270f24ef4f5d22b122 ;;
        linux-x64) f=hax-0.7.0-linux-x86_64.tar.gz; sha=970183b80f1e7e8d2d4f8d9905234f415deb21cc80f111fbb5cc85bb9575fa3e ;;
        *) echo "warning: hax 0.7.0 has no $plat build; skipping it" >&2; return 0 ;;
    esac
    fetch "https://github.com/OleksandrChekhovskyi/hax/releases/download/v0.7.0/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$PREFIX/bin" hax
    rm -f "$dl/$f"
    chmod +x "$PREFIX/bin/hax"
}

install_jcode() {
    [ "$plat" = win32-x64 ] && { win_install jcode https://github.com/1jehuang/jcode/releases/download/v0.99.1/jcode-windows-x86_64.exe 142052584016b44fe12dc21b9fa7d0f67771fc9bcc9d1565c69f4318fae73586; return; }
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
    [ "$plat" = win32-x64 ] && { win_install reasonix https://github.com/esengine/DeepSeek-Reasonix/releases/download/studio-v2.61.0/reasonix-windows-amd64.zip 50062ac360a5d2351f0568b700cab90eda6d57b2329c43809e37c5bbb02284ac reasonix.exe; return; }
    case "$plat" in
        darwin-arm64) f=reasonix-darwin-arm64.tar.gz; sha=7318b46b28c2a05d53ea06b5f3346aa7ee86428e6ee76024ea728f1a47714d0d ;;
        darwin-x64) f=reasonix-darwin-amd64.tar.gz; sha=8320aefaceb2685102fb0fff532661e9ea5f6acfffe005db778fc617598f68f1 ;;
        linux-arm64) f=reasonix-linux-arm64.tar.gz; sha=08ce828507427f3f0e475e2b0bf5e71944e30e49b197fc8bd2ab8dc25983f174 ;;
        linux-x64) f=reasonix-linux-amd64.tar.gz; sha=ceb15ec2f5509325a9f2f314b28758286a88492064a40f12d1ced1440f45fa0b ;;
    esac
    fetch "https://github.com/esengine/DeepSeek-Reasonix/releases/download/studio-v2.61.0/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/reasonix" && tar -xzf "$dl/$f" -C "$dl/reasonix" reasonix
    rm -f "$PREFIX/bin/reasonix"
    cat "$dl/reasonix/reasonix" > "$PREFIX/bin/reasonix"
    rm -rf "$dl/$f" "$dl/reasonix"
    chmod +x "$PREFIX/bin/reasonix"
}

# oh-my-pi ships bare executables (a Bun single-file build).
install_omp() {
    [ "$plat" = win32-x64 ] && { win_install omp https://github.com/can1357/oh-my-pi/releases/download/v18.20.0/omp-windows-x64.exe 1b6c7bda8241bc7d948495539f90ec47e6f30d1fec72b6ee097a67a1fc8d8e48; return; }
    case "$plat" in
        darwin-arm64) f=omp-darwin-arm64; sha=2b1309b06a743ae939708f939b63f75c7a436ed08c7953309f0e387e0c793ead ;;
        darwin-x64) f=omp-darwin-x64; sha=dcd8387f88d32a599451c21c3f402bdc2364243e9e6e5630ff7eec7a8638c4f6 ;;
        linux-arm64) f=omp-linux-arm64; sha=8b5e197db7c58b7ebabf83c6f03597f89bae3a766a84c6481b3a942a125f5e22 ;;
        linux-x64) f=omp-linux-x64; sha=c8694be8c6e6a1f45e3636dd8a8e9eaa78878ad629a89000b403ec5e456d3f89 ;;
    esac
    fetch "https://github.com/can1357/oh-my-pi/releases/download/v18.20.0/$f" "$dl/$f" "$sha"
    rm -f "$PREFIX/bin/omp"
    cat "$dl/$f" > "$PREFIX/bin/omp"
    rm -f "$dl/$f"
    chmod +x "$PREFIX/bin/omp"
}

# Open Interpreter is a Codex fork and keeps Codex's asset names.
install_interpreter() {
    [ "$plat" = win32-x64 ] && { win_install interpreter https://github.com/openinterpreter/openinterpreter/releases/download/rust-v0.0.61/codex-x86_64-pc-windows-msvc.exe 6c4d98d3b75630b7967b47c461eb1e5f1a64bda0072bbed59abc3b2b5bd7b4d2; return; }
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=2def67f2d42c9b4ec098e9f41b373bbbd9db4f0bcf6c63987a6e157b3d38309e ;;
        darwin-x64) t=x86_64-apple-darwin; sha=46839802355c824a91b13f30658b4fa39a3a49f4149e33e66dc243ae6b709ef7 ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=4eb8dc3718b862ed8a2a7d10143932eb60a8ef30088ee0071549dfad64ee31fb ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=2dfb4798255e87f7c4520240312c8a4bba96cea4369b1ef55bff1174fd730f7f ;;
    esac
    f=codex-$t.tar.gz
    fetch "https://github.com/openinterpreter/openinterpreter/releases/download/rust-v0.0.61/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/interpreter" && tar -xzf "$dl/$f" -C "$dl/interpreter"
    rm -f "$PREFIX/bin/interpreter"
    cat "$dl/interpreter/codex-$t" > "$PREFIX/bin/interpreter"
    rm -rf "$dl/$f" "$dl/interpreter"
    chmod +x "$PREFIX/bin/interpreter"
}

# fx ships a tarball per platform with its own .sha256 next to it.
install_fx() {
    case "$plat" in
        darwin-arm64) f=fx-macos-aarch64.tar.gz; sha=2158a8d42e77457a774400d225d9802bb6c0e60a0bb0674a1116bc31252490d6 ;;
        darwin-x64) f=fx-macos-x86_64.tar.gz; sha=b287974f97a0879f50b4439c46537fcd44b83326c11a230d87f596073f8d8d9b ;;
        linux-arm64) f=fx-linux-aarch64.tar.gz; sha=ca9441b104357e2105039dbfd4c2eaf0d6ee65a84085f23f51e880c95cbf46af ;;
        linux-x64) f=fx-linux-x86_64.tar.gz; sha=f0fb822c7be546c80bcc89d50521bc1454435e0c6f586e8420c4e2b84fa80599 ;;
    esac
    fetch "https://github.com/vercel-labs/fx/releases/download/v0.0.16/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/fx" && tar -xzf "$dl/$f" -C "$dl/fx" fx
    rm -f "$PREFIX/bin/fx"
    cat "$dl/fx/fx" > "$PREFIX/bin/fx"
    rm -rf "$dl/$f" "$dl/fx"
    chmod +x "$PREFIX/bin/fx"
}

# Grok Build ships bare executables from x.ai with no published checksums (its
# own installer checks none). They're pinned only when the same bytes come from
# both of its origins, x.ai and its Google Cloud Storage bucket; the macOS
# build is also signed by xAI (team 5Y6N3AJ54S).
install_grok() {
    [ "$plat" = win32-x64 ] && { win_install grok https://x.ai/cli/grok-1.0.77-windows-x86_64.exe 6b757512d240a6439535ca75aad039e581d00f17ba8e937112fd0dbaadf1bc81; return; }
    case "$plat" in
        darwin-arm64) p=macos-aarch64; sha=197c66a63e5ac46e07450b0ca21d141ce665050a412180f185dadfae1c7a5b2a ;;
        darwin-x64) p=macos-x86_64; sha=7728f79ea713ae67a4fa4736dcf808f6b386d9642202aea1df695073fa56675a ;;
        linux-arm64) p=linux-aarch64; sha=b30eee14a656124ef3c9da8577b5e783ef2cffabeb2b679c5c49633e77eed574 ;;
        linux-x64) p=linux-x86_64; sha=b702950aa5827d855e493278ab6215a4e0f5bceb5bba6c6243a9f55cdd143b0a ;;
    esac
    fetch "https://x.ai/cli/grok-1.0.77-$p" "$dl/grok" "$sha"
    rm -f "$PREFIX/bin/grok"
    cat "$dl/grok" > "$PREFIX/bin/grok"
    rm -f "$dl/grok"
    chmod +x "$PREFIX/bin/grok"
}

bin_agents="chanto goose opencode codewhale zerostack hax jcode reasonix omp interpreter grok fx"

# Those with a Windows build pinned (the rest are below the published bar).
win_agents="chanto goose opencode codewhale jcode reasonix omp interpreter grok"

install_bin() {
    bin_setup
    agents=$bin_agents
    [ "$plat" = win32-x64 ] && agents=$win_agents
    for a in $agents; do "install_$a"; done
}

case "$only" in
    all) install_npm; install_uv; install_bin ;;
    npm) install_npm ;;
    uv) install_uv ;;
    bin) install_bin ;;
    *)
        # One binary agent by name, e.g. `./install-agents.sh hax`.
        case " $bin_agents " in
            *" $only "*)
                bin_setup
                if [ "$plat" = win32-x64 ] && ! case " $win_agents " in *" $only "*) true ;; *) false ;; esac; then
                    echo "error: no Windows build of $only is pinned" >&2; exit 1
                fi
                "install_$only" ;;
            *) echo "usage: $0 [npm|uv|bin|<binary agent>]" >&2; exit 2 ;;
        esac ;;
esac

echo "Installed into $PREFIX (uv tools in ~/.local/share/uv/tools)."
echo "Check what a run will use: python3 run.py --estimate --agents <names>"

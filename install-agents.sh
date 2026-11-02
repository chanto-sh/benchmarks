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
    uv tool install --force --python 3.12 mistral-vibe==3.0.4
}

# Standalone binaries, each a GitHub release (or official build) checked
# against a pinned SHA-256:
#   Chanto 0.1.15 (checksums from the release's signed SHA256SUMS);
#   Goose 1.57.0;
#   opencode 2.2.5 (hashed from opencode.ai as first fetched over HTTPS);
#   jcode 0.99.1, DeepSeek-Reasonix 2.56.1, oh-my-pi 18.14.2, Open Interpreter 0.0.57,
#   fx 0.0.15 (checksums from each GitHub release's own SHA-256 digests);
#   Grok Build 1.0.70 (see install_grok);
#   Codewhale 0.10.2, zerostack 1.8.5, hax 0.6.1 (checksums
#   cross-checked against each release's own SHA-256 manifest).
# On Windows (win32-x64) each agent's .exe comes through win_install, pinned
# from the same sources: GitHub's SHA-256 digest of each release file, Chanto's
# signed SHA256SUMS, and Grok Build's matching bytes from both origins. opencode
# 2.2.5 publishes no checksum for Windows and has no second source (its
# Homebrew formula has no Windows build; npm and Scoop stop at 1.19.5), so its
# pin is the opencode.ai download's own SHA-256 as first fetched over HTTPS.
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

CHANTO_VERSION=0.1.15

install_chanto() {
    [ "$plat" = win32-x64 ] && { win_install chanto "https://github.com/chanto-sh/chanto/releases/download/v$CHANTO_VERSION/chanto-v$CHANTO_VERSION-x86_64-pc-windows-msvc.zip" 49a18bca2a20c444f9873cdf8387e4532596af2c4f8146a9a124f5f2f62ab28f chanto.exe; return; }
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=48ed3bb19e29be3baf5f3fc8a135022d2c6dbaf3aaf78ee26bb7e3aceed5867a ;;
        darwin-x64) t=x86_64-apple-darwin; sha=f3b1c16fda2b221955b6e3b0243e8cb1bcfe59eb26212e50ab92cf2dd268d487 ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=6200dc99dbd65dbf4ddfd0467ea549d16150e93210db7dcd2584ffcd66653b6c ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=af4ab5fab4f61060306aba3ba097c6715135d09296b0e9f1c9b866e904150d0f ;;
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
    [ "$plat" = win32-x64 ] && { win_install goose https://github.com/block/goose/releases/download/v1.57.0/goose-x86_64-pc-windows-msvc.zip 1ab2117ceec37f95be4d3ad0cdb921d3e97fd8b0fa244046631ecf4b7619d502 goose.exe; return; }
    case "$plat" in
        darwin-arm64) f=goose-aarch64-apple-darwin.tar.gz; sha=80d43c49b77302777e9d2fe32faf3c40c1028dafbea1e0a39b0378404a8a074b ;;
        darwin-x64) f=goose-x86_64-apple-darwin.tar.gz; sha=5ad5594246841c759b34966e09ca421c09151b589183a8f1720e15e8395834ae ;;
        linux-arm64) f=goose-aarch64-unknown-linux-gnu.tar.gz; sha=c32605acfd560aeb2adbf17ec359cc0217e28022a7e647b35a6af5dcfca91749 ;;
        linux-x64) f=goose-x86_64-unknown-linux-gnu.tar.gz; sha=10eb96cb6a159b6e1d38eeedbef6ab64cd28168aad91948f1fa5c34eefdf98e3 ;;
    esac
    fetch "https://github.com/block/goose/releases/download/v1.57.0/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$PREFIX/bin" ./goose
    chmod +x "$PREFIX/bin/goose"
}

install_opencode() {
    [ "$plat" = win32-x64 ] && { win_install opencode https://opencode.ai/files/bin/2.2.5/opencode-windows-x64-baseline.zip 3acca208ad79add59aed13d07b7e08ddf24e0adbbb7f44a9131408d7b3ca67cd opencode.exe; return; }
    case "$plat" in
        darwin-arm64) f=opencode-darwin-arm64.zip; sha=25ba9908979fa7d764792c82589b4b5768ab1511154e0317d98aa77d216ce767 ;;
        darwin-x64) f=opencode-darwin-x64-baseline.zip; sha=b83ab73b3eb7b08f580f597eba8a7bcd886d2efa2ebf90405ad74ef54da02f71 ;;
        linux-arm64) f=opencode-linux-arm64.tar.gz; sha=5a528f42caf576c6cdece6a191eb273d3db54effa5518e0402684d8f8026aeb6 ;;
        linux-x64) f=opencode-linux-x64-baseline.tar.gz; sha=09f44302c10fd036912f59c81fd1aef5df45dd06f649197f9dfc9bbe2a79614e ;;
    esac
    fetch "https://opencode.ai/files/bin/2.2.5/$f" "$dl/$f" "$sha"
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
    [ "$plat" = win32-x64 ] && { win_install reasonix https://github.com/esengine/DeepSeek-Reasonix/releases/download/studio-v2.56.1/reasonix-windows-amd64.zip 217f91c11313fbb3363d6de645d4b382e4b8186ee351c347a193c3fc507babee reasonix.exe; return; }
    case "$plat" in
        darwin-arm64) f=reasonix-darwin-arm64.tar.gz; sha=943e93b24bd8a3dfedd4ce4e5be62ff9e265946ef7f8501846ffec8907f7e79a ;;
        darwin-x64) f=reasonix-darwin-amd64.tar.gz; sha=fb73e359ca4937d5dcb157d7c10a2054f7dcf4bd43a7d74beb118d9a6ce57a20 ;;
        linux-arm64) f=reasonix-linux-arm64.tar.gz; sha=0f3cf9ed0c7b799249aada9ed1691e851b87c314982db8e50516b0f6f3a59851 ;;
        linux-x64) f=reasonix-linux-amd64.tar.gz; sha=c79933b8efc8d755ccb1873874ae91aaa707ac4044bd05fa517131329d0c0547 ;;
    esac
    fetch "https://github.com/esengine/DeepSeek-Reasonix/releases/download/studio-v2.56.1/$f" "$dl/$f" "$sha"
    mkdir -p "$dl/reasonix" && tar -xzf "$dl/$f" -C "$dl/reasonix" reasonix
    rm -f "$PREFIX/bin/reasonix"
    cat "$dl/reasonix/reasonix" > "$PREFIX/bin/reasonix"
    rm -rf "$dl/$f" "$dl/reasonix"
    chmod +x "$PREFIX/bin/reasonix"
}

# oh-my-pi ships bare executables (a Bun single-file build).
install_omp() {
    [ "$plat" = win32-x64 ] && { win_install omp https://github.com/can1357/oh-my-pi/releases/download/v18.14.2/omp-windows-x64.exe aa04e4ff3b2d97d604839edf1bcf5a0085818389d9fc8c1a18875ee7b5e3b0f8; return; }
    case "$plat" in
        darwin-arm64) f=omp-darwin-arm64; sha=9b7bda0bd8ec8d1fd8f8deda076180deef2d4921ee60e7d2f39044ee7d9437ee ;;
        darwin-x64) f=omp-darwin-x64; sha=62835e51acc0f07d19493da736b7215d3224fd5099754b7e42c3b0fdc2eb7f45 ;;
        linux-arm64) f=omp-linux-arm64; sha=afbdf04be3ddbe34a07e91c913ddb6d335a3a0210f520ac5a197a245888ad63e ;;
        linux-x64) f=omp-linux-x64; sha=cde0bc4ac8ec333c4880039a5242ff33dbfc6544747d67aeb99bb077874aeec1 ;;
    esac
    fetch "https://github.com/can1357/oh-my-pi/releases/download/v18.14.2/$f" "$dl/$f" "$sha"
    rm -f "$PREFIX/bin/omp"
    cat "$dl/$f" > "$PREFIX/bin/omp"
    rm -f "$dl/$f"
    chmod +x "$PREFIX/bin/omp"
}

# Open Interpreter is a Codex fork and keeps Codex's asset names.
install_interpreter() {
    [ "$plat" = win32-x64 ] && { win_install interpreter https://github.com/openinterpreter/openinterpreter/releases/download/rust-v0.0.57/codex-x86_64-pc-windows-msvc.exe 90d10a8f93e07953b04b12801c3b752477081d0cde23236a0192d677aa140cf4; return; }
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=9a1c977cb675e59b0f46171dd3124c9ad05d4ee382c469c77aa6c40a08eb8d06 ;;
        darwin-x64) t=x86_64-apple-darwin; sha=14b3a38484115ff6c051aa27e57da3c185b01495ed39f7bc0e15756b512e185d ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=d1a2dd60f9162717214e99f623516994e1d4d6f3ac9a37e8536817842b463beb ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=4573d09f7096e2e6786d83144243e480db1627ca5b6adb4dd697b3b977d6a176 ;;
    esac
    f=codex-$t.tar.gz
    fetch "https://github.com/openinterpreter/openinterpreter/releases/download/rust-v0.0.57/$f" "$dl/$f" "$sha"
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
    [ "$plat" = win32-x64 ] && { win_install grok https://x.ai/cli/grok-1.0.70-windows-x86_64.exe 1e03c16cf2bd4626a79d6b1ea1430f88c38e0c8ec75edd283a60de11296ba326; return; }
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

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
    uv tool install --force --python 3.12 mini-swe-agent==2.4.6 --with litellm==1.110.3
    uv tool install --force --python 3.12 mistral-vibe==3.1.5
}

# Standalone binaries, each pinned by version and SHA-256:
#   Chanto 0.1.27 (checksums from the release's signed SHA256SUMS);
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

CHANTO_VERSION=0.1.27

install_chanto() {
    [ "$plat" = win32-x64 ] && { win_install chanto "https://github.com/chanto-sh/chanto/releases/download/v$CHANTO_VERSION/chanto-v$CHANTO_VERSION-x86_64-pc-windows-msvc.zip" 58db46597fd5f33eb220a406980008d4f08edd5bdb6ec0af068d080b8b974a40 chanto.exe; return; }
    case "$plat" in
        darwin-arm64) t=aarch64-apple-darwin; sha=786e9015a45e1c962c25393ddfea341dd3ca5c993abc712063d945a54efbc8aa ;;
        darwin-x64) t=x86_64-apple-darwin; sha=79683dd64d25bf77e54189d0afba4a42fc477abd30ad1f7bcf55a532e20033d4 ;;
        linux-arm64) t=aarch64-unknown-linux-musl; sha=e9b8c2fb316bcd2a4499b55c049b275e67f9bad051427c5221536c511174ab1e ;;
        linux-x64) t=x86_64-unknown-linux-musl; sha=ca71195fcadc83b8053cd7e5164919fbd2c34f9a5b3e291181945119dbf1b049 ;;
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
    [ "$plat" = win32-x64 ] && { win_install goose https://github.com/block/goose/releases/download/v1.60.2/goose-x86_64-pc-windows-msvc.zip 5b838ab498f7a6b121fab621b99d39a480458c373f16be7f7ce7869e9bc54888 goose.exe; return; }
    case "$plat" in
        darwin-arm64) f=goose-aarch64-apple-darwin.tar.gz; sha=3a317d80997f40bba4c6bd9edbe9a3381e88badea7ff5064fe9d757512006511 ;;
        darwin-x64) f=goose-x86_64-apple-darwin.tar.gz; sha=82d9f11c2ee6d4021a05a9471c5112ebc67dc77519d77cce0cc12953affe3ed1 ;;
        linux-arm64) f=goose-aarch64-unknown-linux-gnu.tar.gz; sha=7e74d796e93b89df374715dc669149cb634f74d778de0b87bb7c031b5b093731 ;;
        linux-x64) f=goose-x86_64-unknown-linux-gnu.tar.gz; sha=5f6e463621a8428617ae4870eecee7a00a253e9bbfccb6340dfaa4f0ec2aaf32 ;;
    esac
    fetch "https://github.com/block/goose/releases/download/v1.60.2/$f" "$dl/$f" "$sha"
    tar -xzf "$dl/$f" -C "$PREFIX/bin" ./goose
    chmod +x "$PREFIX/bin/goose"
}

install_opencode() {
    [ "$plat" = win32-x64 ] && { win_install opencode https://github.com/sst/opencode/releases/download/v2.4.1/opencode-windows-x64-baseline.zip 40c4f842398abcba3837d554a2b0ddd9a11c5fae667f198e0bb716d101a2aab4 opencode.exe; return; }
    case "$plat" in
        darwin-arm64) f=opencode-darwin-arm64.zip; sha=95a101eda95108478f1db43cff8fcbd4811f6c0e79af1e167301843c6a48d731 ;;
        darwin-x64) f=opencode-darwin-x64-baseline.zip; sha=3dd6612423b69f7f282866112d99b6d690c8e07f27375b227f6a6ee4e652f5b5 ;;
        linux-arm64) f=opencode-linux-arm64.tar.gz; sha=cb28cf94541aeb62a4b2ea5997a99b5dd6bae595a772f36fbe279299f2032a4f ;;
        linux-x64) f=opencode-linux-x64-baseline.tar.gz; sha=9ddd18e3faf64eaeccf6a0fcbc96a5c7a14520ae5fd5b61e5be51d894f478b47 ;;
    esac
    fetch "https://github.com/sst/opencode/releases/download/v2.4.1/$f" "$dl/$f" "$sha"
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
    [ "$plat" = win32-x64 ] && { win_install codewhale https://github.com/codewhale-hq/Codewhale/releases/download/v0.10.4/codewhale-windows-x64.exe 9b779506b8600ed8fe05c661e2769bcce5166fa6a59179c07dcdb34fad053a93; return; }
    case "$plat" in
        darwin-arm64) f=codewhale-macos-arm64; sha=1c4e654b4574f82504cb233e96501e7b4aaec0a82dfff07490f7472cb14e8891 ;;
        darwin-x64) f=codewhale-macos-x64; sha=6a56fc354d2dd3a853a8eb768ccbac086b591796e33b673522ffa94c6434aa36 ;;
        linux-arm64) f=codewhale-linux-arm64; sha=4e809350514e7eb161e121227eca4a3ef6c753d4685d697b66d0819a2a3844a2 ;;
        linux-x64) f=codewhale-linux-x64; sha=81d82a15cec265ea72f76515f991ced07aa3fbe377aa3dfb53b70fe4ea30ce60 ;;
    esac
    fetch "https://github.com/codewhale-hq/Codewhale/releases/download/v0.10.4/$f" "$dl/$f" "$sha"
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
    [ "$plat" = win32-x64 ] && { win_install jcode https://github.com/1jehuang/jcode/releases/download/v1.0.3/jcode-windows-x86_64.exe 3c929e46b2facc14a21032f845d26c0e2a80a7a9d008cb64c4845fa4434d30dd; return; }
    case "$plat" in
        darwin-arm64) f=jcode-macos-aarch64.tar.gz; sha=274396799d2c60600ce3e4890abe78439c1882017eedfc272ce30b1730c5b74b ;;
        darwin-x64) f=jcode-macos-x86_64.tar.gz; sha=1e9833027eeac661662c15d4d7cd568ea394a399470e131f7ad40dd4dda5198e ;;
        linux-arm64) f=jcode-linux-aarch64.tar.gz; sha=c76cec0b9b98458aca9d1a0bcfa92d330459b7cfef12700c19f130881129ce8f ;;
        linux-x64) f=jcode-linux-x86_64.tar.gz; sha=7283a4417fed877229fd89049173a3bb469368a3dec37ca2cc31c4895fb3a6ad ;;
    esac
    fetch "https://github.com/1jehuang/jcode/releases/download/v1.0.3/$f" "$dl/$f" "$sha"
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
    [ "$plat" = win32-x64 ] && { win_install omp https://github.com/can1357/oh-my-pi/releases/download/v19.1.1/omp-windows-x64.exe 4e18f472975bb87f9b1992f1d5981b9a1403fd559cdb3eb96f1f1a7d709096ef; return; }
    case "$plat" in
        darwin-arm64) f=omp-darwin-arm64; sha=d5a3324acd98375a01698a1b0c018be48caed2956c8aa9044ad137fe43bc0400 ;;
        darwin-x64) f=omp-darwin-x64; sha=6ffecb22a9fe01a98f90f91a2ef04a697850a23bf4dde83adad2fe80e51a8353 ;;
        linux-arm64) f=omp-linux-arm64; sha=f022f720c4899eb24c6e5e34dcbbae98ae05f5532bb03e97dffc02cfc8dd9a6f ;;
        linux-x64) f=omp-linux-x64; sha=04e9490f9394da6d6804474cc2e41eb3d18f8e26215df4b34bdd4ad4c0d8a401 ;;
    esac
    fetch "https://github.com/can1357/oh-my-pi/releases/download/v19.1.1/$f" "$dl/$f" "$sha"
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
        darwin-arm64) f=fx-macos-aarch64.tar.gz; sha=5cacb5b3624a79db8fd4e31dcbc59d6a933d7e5ed4c397776d95df6b618296a9 ;;
        darwin-x64) f=fx-macos-x86_64.tar.gz; sha=984eef6632d7bd27ff7b75befb52b9db32c25287905009db5822f6a669861fec ;;
        linux-arm64) f=fx-linux-aarch64.tar.gz; sha=b4633b8987ec43f1b9454e4629f3b5a4f1e086aae36b84ae4fefeacd6a53761f ;;
        linux-x64) f=fx-linux-x86_64.tar.gz; sha=78c155d59fa59e42fd56d93037fd75041868c9c67865e8c7f0ca6dcdfac23e75 ;;
    esac
    fetch "https://github.com/vercel-labs/fx/releases/download/v0.0.17/$f" "$dl/$f" "$sha"
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
    [ "$plat" = win32-x64 ] && { win_install grok https://x.ai/cli/grok-1.0.92-windows-x86_64.exe 060e51f93743b540e59c5cf9c81c0ce7b48b61c263f09235d981a6ababb1c9d7; return; }
    case "$plat" in
        darwin-arm64) p=macos-aarch64; sha=8b5f67b24f2cc9a4341d8e2eb7f67e3228d7d647ed04752a4f932f7133e5ab08 ;;
        darwin-x64) p=macos-x86_64; sha=66b7a3ef1d647280ac649b68d89b5a3d4800b1ae9df76707c011e2d400858ea9 ;;
        linux-arm64) p=linux-aarch64; sha=8c74f1dc6cdc1befff6b9faada06bec4cf6759d04f2a60cdc28ece5ff696b44f ;;
        linux-x64) p=linux-x86_64; sha=add4d201dbf2c0bd6077a36feb55a76939de30bae48dbb06f16b2307d38ceacb ;;
    esac
    fetch "https://x.ai/cli/grok-1.0.92-$p" "$dl/grok" "$sha"
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

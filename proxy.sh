#!/bin/bash
# Run the benchmark proxy: proxy.sh [upstream-model]
#   proxy.sh deepseek/deepseek-flash
#   proxy.sh mistral/codestral-latest
#   proxy.sh openrouter/qwen/qwen3.5-9b
# The key is read from ~/.config/chanto-bench/<provider>_key (or BENCH_UPSTREAM_KEY).
# Port: BENCH_PROXY_PORT (default 4000), to run two providers side by side.
# Spending limits: use a prepaid provider account, and run.py
# --min-balance (DeepSeek) to stop before it runs dry. LiteLLM's own budget
# needs a database, so it isn't used here.
#
# litellm is pinned (BENCH_LITELLM_PIN) to a known-good release: v1.107.0
# (PyPI/Docker, 2026-10-21) shipped a credential stealer, so a stray
# `uv tool upgrade litellm` must not pull a compromised build into a run.
# Install/repair with: uv tool install "litellm[proxy]==$BENCH_LITELLM_PIN" --force
set -e
BENCH_LITELLM_PIN="${BENCH_LITELLM_PIN:-1.106.2}"
# Read the installed version from uv's record, never by executing litellm — a
# compromised build runs its payload on any Python startup, `--version` included.
have="$(uv tool list 2>/dev/null | awk '/^litellm /{print $2}' | tr -d 'v')"
case "$have" in
  1.107.0)
    echo "refusing litellm $have: known-compromised release (2026-10-21)." >&2
    echo "reinstall: uv tool install \"litellm[proxy]==$BENCH_LITELLM_PIN\" --force" >&2
    exit 1 ;;
  "$BENCH_LITELLM_PIN") : ;;
  "") echo "warning: could not read litellm's version from 'uv tool list'; skipping the pin check" >&2 ;;
  *) echo "warning: litellm $have is not the pinned $BENCH_LITELLM_PIN (pin: uv tool install \"litellm[proxy]==$BENCH_LITELLM_PIN\" --force)" >&2 ;;
esac
export BENCH_UPSTREAM="${1:-deepseek/deepseek-flash}"
provider="${BENCH_UPSTREAM%%/*}"
export BENCH_UPSTREAM_KEY="${BENCH_UPSTREAM_KEY:-$(cat ~/.config/chanto-bench/${provider}_key)}"
# USD per token (input, output), so the proxy log shows spend. Off-peak rates;
# DeepSeek's peak rate (01:00-04:00 and 06:00-10:00 UTC Mon-Fri) is double.
# `deepseek-flash` serves DeepSeek-V4.1-Flash-1017 (V4-Flash is retired).
case "$BENCH_UPSTREAM" in
  deepseek/deepseek-flash|deepseek/deepseek-v4-flash) cost_in=0.00000015; cost_out=0.0000006 ;;
  deepseek/deepseek-v4-pro) cost_in=0.00000066; cost_out=0.00000198 ;;
  openrouter/qwen/qwen3.5-9b) cost_in=0.0000001; cost_out=0.00000015 ;;
  *) cost_in=0; cost_out=0 ;;
esac
# The config and its no_search.py hook go in one directory: LiteLLM loads
# callbacks from beside the config file.
dir="$(mktemp -d -t bench-litellm)"
cfg="$dir/litellm.yaml"
sed -e "s/__COST_IN__/$cost_in/" -e "s/__COST_OUT__/$cost_out/" "$(dirname "$0")/litellm.yaml" > "$cfg"
cp "$(dirname "$0")/no_search.py" "$dir/"
exec litellm --config "$cfg" --port "${BENCH_PROXY_PORT:-4000}"

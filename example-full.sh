#!/bin/bash
# The full representative run, end to end: every coding tier, every coding
# agent the runner supports, all on one model — DeepSeek 4.1 Flash (the
# `deepseek-flash` alias, which serves DeepSeek-V4.1-Flash-1017).
#
#   example-full.sh --estimate   # print the projection and stop
#   example-full.sh              # estimate, then run
#
# Override with env: MODEL, AGENTS, TIERS, SHARDS, TIMEOUT, MIN_BALANCE, CTX.
# The task set is the whole coding suite: core (polyglot katas), medium
# (hand-written), hard (the 25 SWE-bench Lite issues) and beyond (the honesty
# tier). Add `showcase` to TIERS for the answer-producing tasks (data analysis,
# root-causing, docs), which are not part of the coding score.
set -euo pipefail
cd "$(dirname "$0")"

MODEL="${MODEL:-deepseek/deepseek-flash}"
AGENTS="${AGENTS:-chanto,chanto-verify,claude,codex,opencode,aider,goose,pi,crush,qwen,kilo,forge,cline}"
TIERS="${TIERS:-core,medium,hard,beyond}"
SHARDS="${SHARDS:-2}"
TIMEOUT="${TIMEOUT:-1200}"
MIN_BALANCE="${MIN_BALANCE:-3}"
CTX="${CTX:-131072}"
# The Chanto checkout under test: a sibling clone unless CHANTO_REPO says otherwise.
export BENCH_CHANTO_BIN="${BENCH_CHANTO_BIN:-${CHANTO_REPO:-$PWD/../chanto}/target/release/chanto}"

[ -x "$BENCH_CHANTO_BIN" ] || {
  echo "no chanto binary at $BENCH_CHANTO_BIN — run \`cargo build --release\` in the Chanto checkout" >&2; exit 1; }

echo "chanto binary : $BENCH_CHANTO_BIN"
echo "model          : $MODEL   (one model for every agent)"
echo "agents         : $AGENTS"
echo "tiers          : $TIERS"
echo

# What the run will cost, averaged from results/*.json. Runs nothing.
# `--model` here names the *upstream* so --estimate can price it; the run below
# talks to the proxy, whose model every agent requests as `bench-model`.
python3 run.py --estimate --model "$MODEL" --tier "$TIERS" --agents "$AGENTS"
if [ "${1:-}" = "--estimate" ]; then exit 0; fi

[ -f "$HOME/.config/chanto-bench/deepseek_key" ] || {
  echo "put your DeepSeek key in ~/.config/chanto-bench/deepseek_key" >&2; exit 1; }

# One proxy for every agent; one meter that counts every agent's tokens.
./proxy.sh "$MODEL" & PROXY=$!
python3 meter.py --port 4100 --upstream http://localhost:4000 --log meter.jsonl & METER=$!
shards_dir="$(mktemp -d)"
trap 'kill "$PROXY" "$METER" 2>/dev/null || true; rm -rf "$shards_dir"' EXIT
ready=0
for _ in $(seq 60); do
  if curl -sf -o /dev/null http://localhost:4000/health/liveliness && curl -sf -o /dev/null http://localhost:4100/; then ready=1; break; fi
  sleep 1
done
[ "$ready" = 1 ] || { echo "proxy/meter did not come up in 60s" >&2; exit 1; }

# Split every coding task across SHARDS, interleaved so each shard sees a mix of tiers.
python3 - "$TIERS" "$SHARDS" "$shards_dir" <<'PY'
import sys
sys.path.insert(0, ".")
import run
tiers, shards, dest = sys.argv[1].split(","), int(sys.argv[2]), sys.argv[3]
tasks = run.select_tasks(tiers, None)
for s in range(shards):
    mine = tasks[s::shards]
    if mine:
        open(f"{dest}/shard{s}.txt", "w").write(",".join(mine))
print(f"{len(tasks)} tasks across {shards} shard(s)", file=sys.stderr)
PY
echo "running; Ctrl-C to stop (results land in results/)"

pids=()
for f in "$shards_dir"/shard*.txt; do
  base="$(basename "$f")"; s="${base%.txt}"; s="${s#shard}"
  BENCH_WORK="$HOME/.local/share/chanto-bench/work-example-$s" \
  python3 run.py \
    --api http://localhost:4000 --meter http://localhost:4100 --meter-log meter.jsonl \
    --model bench-model --ctx "$CTX" --offline --timeout "$TIMEOUT" --min-balance "$MIN_BALANCE" \
    --seed "$((1200 + s))" --agents "$AGENTS" --tasks "$(cat "$f")" &
  pids+=($!)
done

status=0
for p in "${pids[@]}"; do wait "$p" || status=$?; done
rm -rf "$shards_dir"
exit "$status"

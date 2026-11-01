#!/bin/bash
# One job of .github/workflows/suite.yml: suite_job.sh start | run | check
set -eu
RESULTS_OUT=$RUNNER_TEMP/suite
METER_LOG=$RUNNER_TEMP/meter.jsonl
PROXY_PORT=4010

wait_for() {
    for _ in $(seq 60); do
        curl -s -o /dev/null "http://127.0.0.1:$1/" && return 0
        sleep 1
    done
    echo "nothing listening on port $1" >&2
    exit 1
}

case "$1" in
start)
    if [ "$MOCK" = true ]; then
        nohup python3 -u stressmock.py > "$RUNNER_TEMP/model.log" 2>&1 &
        for _ in $(seq 30); do
            grep -q '^PORT ' "$RUNNER_TEMP/model.log" && break
            sleep 1
        done
        PROXY_PORT=$(awk '/^PORT /{print $2; exit}' "$RUNNER_TEMP/model.log")
    else
        [ -n "${BENCH_UPSTREAM_KEY:-}" ] || { echo "DEEPSEEK_API_KEY isn't set in the benchmark environment" >&2; exit 1; }
        uv tool install --python 3.12 "litellm[proxy]==1.106.2"
        BENCH_PROXY_PORT=$PROXY_PORT nohup ./proxy.sh deepseek/deepseek-flash > "$RUNNER_TEMP/model.log" 2>&1 &
    fi
    wait_for "$PROXY_PORT"
    echo "$PROXY_PORT" > "$RUNNER_TEMP/model.port"
    nohup python3 meter.py --port 4101 --upstream "http://localhost:$PROXY_PORT" --log "$METER_LOG" > "$RUNNER_TEMP/meter.log" 2>&1 &
    wait_for 4101
    ;;
run)
    prefix=${BENCH_HOME:-$HOME/.local/share/chanto-bench}
    export BENCH_CHANTO_BIN=$prefix/bin/chanto
    ctx=()
    [ "$MOCK" = true ] && ctx=(--ctx 200000)
    python3 run.py --api "http://localhost:$(cat "$RUNNER_TEMP/model.port")" --meter http://localhost:4101 --meter-log "$METER_LOG" \
        --agents "$AGENTS" --tier core,medium,hard,beyond --tasks "$TASKS" --repeat "$REPEAT" --seed "$SEED" \
        --timeout "$TIMEOUT" --model bench-model "${ctx[@]}"
    ;;
check)
    # Only this job's results: the published ones are in the checkout too.
    mkdir -p "$RESULTS_OUT"
    git ls-files --others --exclude-standard -- results | while read -r f; do
        mkdir -p "$RESULTS_OUT/$(dirname "${f#results/}")"
        cp "$f" "$RESULTS_OUT/${f#results/}"
    done
    if [ -n "${KEY:-}" ] && grep -rqF "$KEY" "$RESULTS_OUT" "$RUNNER_TEMP/model.log" "$RUNNER_TEMP/meter.log"; then
        echo "a result file contains the API key: nothing from this job gets uploaded" >&2
        rm -rf "$RESULTS_OUT"
        exit 1
    fi
    ;;
esac

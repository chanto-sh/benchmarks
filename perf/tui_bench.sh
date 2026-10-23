#!/bin/bash
# usage: tui_bench.sh <binary> ; streams the long mock reply in the TUI, reports CPU seconds
B=$1; H=$(mktemp -d); P=$(mktemp -d); cd "$P"; git init -q
tmux kill-session -t tb 2>/dev/null
tmux new-session -d -s tb -x 160 -y 48 -c "$P" "CHANTO_HOME=$H CHANTO_COMPAT_HOME=$H/c OPENAI_API_KEY=x $B --provider openai --base-url http://127.0.0.1:${PORT:-4302}/v1 --model mock --mode bypassPermissions"
sleep 2
PID=$(pgrep -f "$B --provider openai --base-url http://127.0.0.1:${PORT:-4302}" | head -1)
c0=$(ps -o cputime= -p $PID)
t0=$(python3 -c 'import time;print(time.time())')
tmux send-keys -t tb "write a long doc" Enter
# wait until the reply finished streaming: last section heading visible and idle
for i in $(seq 1 600); do sleep 0.1; tmux capture-pane -t tb -p | grep -q "handle_399" && break; done
t1=$(python3 -c 'import time;print(time.time())')
sleep 1
c1=$(ps -o cputime= -p $PID)
python3 - "$c0" "$c1" "$t0" "$t1" <<'PY'
import sys
def sec(s):
    p=s.strip().split(':'); return sum(float(x)*60**i for i,x in enumerate(reversed(p)))
print(f"TUI stream 30k tokens: wall {float(sys.argv[4])-float(sys.argv[3]):.2f}s  cpu {sec(sys.argv[2])-sec(sys.argv[1]):.2f}s")
PY
tmux kill-session -t tb

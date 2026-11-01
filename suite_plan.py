#!/usr/bin/env python3
"""Split a coding benchmark into jobs for .github/workflows/suite.yml.

    python3 suite_plan.py --agents a,b --tier core,hard --sample 40

Jobs split by task, not by agent: every agent runs a task on the same machine,
interleaved, as run.py does on one machine. Sampling is repeatable and takes
from each tier in proportion, so the task list is known before the run starts.
"""
import argparse, json, math, random

import run

# GitHub ends a job at 6 hours; leave time to install and upload.
JOB_MINUTES = 300
# Minutes one agent takes on a task, on the high side of run.py --estimate's
# averages: a hard task gets a long limit, and running out of time loses runs.
MINUTES = {"core": 1, "medium": 3, "beyond": 3, "hard": 6, "showcase": 3}


def family(task):
    """What a task is drawn from: the project for a SWE-bench task, else its prefix."""
    if task.startswith("swe-"):
        return task[4:].split("__")[0]
    return task.split("-")[0]


def spread(names, n, rng):
    """`n` of `names`, taking from each family in turn."""
    groups = {}
    for t in rng.sample(names, len(names)):
        groups.setdefault(family(t), []).append(t)
    picked = []
    while len(picked) < n:
        for f in sorted(groups):
            if groups[f] and len(picked) < n:
                picked.append(groups[f].pop())
    return picked


def sample(tasks, n, seed):
    """Exactly `n` of `tasks`: each tier in proportion, each spread over its
    projects, so one project can't decide a tier."""
    if not n or n >= len(tasks):
        return tasks
    rng = random.Random(seed)
    tiers = {}
    for t in tasks:
        tiers.setdefault(run.tier_of(t), []).append(t)
    shares = {k: n * len(v) / len(tasks) for k, v in sorted(tiers.items())}
    counts = {k: int(v) for k, v in shares.items()}
    for k in sorted(shares, key=lambda k: counts[k] - shares[k])[:n - sum(counts.values())]:
        counts[k] += 1
    picked = []
    for k, names in sorted(tiers.items()):
        picked += spread(names, counts[k], rng)
    return sorted(picked)


def split(tasks, agents, reps, jobs):
    """Tasks into at most `jobs` jobs of even expected time, or more if they
    wouldn't fit GitHub's limit."""
    cost = {t: MINUTES[run.tier_of(t)] * agents * reps for t in tasks}
    jobs = max(jobs, math.ceil(sum(cost.values()) / JOB_MINUTES), 1)
    groups = []
    # Longest first, each to the emptiest job that has room.
    for t in sorted(tasks, key=lambda t: (-cost[t], t)):
        room = [g for g in groups if g["minutes"] + cost[t] <= JOB_MINUTES]
        if len(groups) < jobs and (not room or min(g["minutes"] for g in room) > 0):
            groups.append({"minutes": cost[t], "tasks": [t]})
        elif room:
            g = min(room, key=lambda g: g["minutes"])
            g["minutes"] += cost[t]
            g["tasks"].append(t)
        else:
            groups.append({"minutes": cost[t], "tasks": [t]})
    return [sorted(g["tasks"]) for g in groups]


def check(files, agents, expect):
    """Print how many runs each agent has. A job that ran out of time loses the
    rest of its runs, and a table with holes must say so."""
    got = dict.fromkeys(agents, 0)
    for f in files:
        for r in json.load(open(f))["results"]:
            got[r["agent"]] = got.get(r["agent"], 0) + 1
    print("| agent | runs | missing |\n|---|---|---|")
    for agent, n in got.items():
        print(f"| {agent} | {n} | {max(expect - n, 0)} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", required=True)
    ap.add_argument("--tier", default=",".join(run.CODING_TIERS))
    ap.add_argument("--tasks", default="")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--check", nargs="+", help="result files to check against --expect")
    ap.add_argument("--expect", type=int, help="runs each agent should have")
    a = ap.parse_args()
    if a.check:
        check(a.check, a.agents.split(","), a.expect)
        return
    tasks = run.select_tasks(a.tier.split(","), a.tasks)
    if not tasks:
        raise SystemExit("no tasks selected")
    tasks = sample(tasks, a.sample, a.seed)
    groups = split(tasks, len(a.agents.split(",")), a.repeat, a.jobs)
    # A matrix holds at most 256 jobs.
    if len(groups) > 256:
        raise SystemExit(f"{len(groups)} jobs is over GitHub's limit of 256")
    print(json.dumps([{"id": i, "tasks": ",".join(g)} for i, g in enumerate(groups)]))


if __name__ == "__main__":
    main()

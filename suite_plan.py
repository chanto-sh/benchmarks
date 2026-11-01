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
# 194 hours over 289 tasks and 23 agents, from run.py --estimate.
MINUTES_PER_RUN = 1.75


def sample(tasks, n, seed):
    """`n` of `tasks`, in proportion to each tier, at least one from each."""
    if not n or n >= len(tasks):
        return tasks
    rng = random.Random(seed)
    tiers = {}
    for t in tasks:
        tiers.setdefault(run.tier_of(t), []).append(t)
    picked = []
    for names in tiers.values():
        picked += rng.sample(names, max(1, round(n * len(names) / len(tasks))))
    return sorted(picked)


def split(tasks, agents, reps, jobs):
    """At most `jobs` jobs if they'd fit the time limit, otherwise more."""
    fits = max(1, int(JOB_MINUTES / (agents * reps * MINUTES_PER_RUN)))
    size = max(math.ceil(len(tasks) / jobs), 1) if jobs else fits
    size = min(size, fits)
    return [tasks[i:i + size] for i in range(0, len(tasks), size)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", required=True)
    ap.add_argument("--tier", default=",".join(run.CODING_TIERS))
    ap.add_argument("--tasks", default="")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
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

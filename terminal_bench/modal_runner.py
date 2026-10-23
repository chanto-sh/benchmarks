"""Run a Harbor job from a Modal container, so it keeps going with this
machine asleep. The trials run in Modal sandboxes as with `harbor run -e
modal`; this only moves Harbor itself off the laptop. Results land in the
`chanto-tb-jobs` volume.

    modal secret create chanto-tb DEEPSEEK_API_KEY=...     # once
    modal run --detach terminal_bench/modal_runner.py \\
        --binary ~/.local/share/chanto-bench/tb-bin --tasks 20

The launcher returns as soon as the job has started.
    modal volume get chanto-tb-jobs / ./tb-jobs             # afterwards

`--task org/name` runs one task instead of a dataset (e.g.
`hello-world/hello-world` to check the setup). `--resume JOB` continues a job already in the volume (finished trials are
kept), e.g. after a timeout.
"""

import os
import shlex
import subprocess
import threading
from pathlib import Path

import modal

HERE = Path(__file__).parent
JOBS = "/jobs"

app = modal.App("chanto-terminal-bench")
volume = modal.Volume.from_name("chanto-tb-jobs", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("uv")
    .run_commands("uv tool install 'harbor[modal]==0.24.0'")
    .env({"PATH": "/root/.local/bin:/usr/local/bin:/usr/bin:/bin", "PYTHONPATH": "/repo"})
    .add_local_file(HERE / "chanto_agent.py", "/repo/bench/terminal_bench/chanto_agent.py")
)


def _keep_committing(stop: threading.Event):
    """Commit the volume every minute, so partial results survive a crash."""
    while not stop.wait(60):
        volume.commit()


@app.function(
    image=image,
    volumes={JOBS: volume},
    secrets=[modal.Secret.from_name("chanto-tb"), modal.Secret.from_name("chanto-tb-modal")],
    timeout=24 * 3600,
    cpu=1.0,
    memory=2048,
)
def run(harbor_args: list[str], binaries: dict[str, bytes]):
    bin_dir = Path("/opt/chanto-bin")
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name, data in binaries.items():
        (bin_dir / name).write_bytes(data)
        (bin_dir / name).chmod(0o755)
    cmd = ["harbor", *harbor_args]
    if harbor_args[0] == "run":
        cmd += ["--ak", f"binary={bin_dir}"]
    print("$", shlex.join(cmd), flush=True)
    # The key comes from the `chanto-tb` secret, not the command line.
    cmd = [a.replace("${DEEPSEEK_API_KEY}", os.environ["DEEPSEEK_API_KEY"]) for a in cmd]
    stop = threading.Event()
    threading.Thread(target=_keep_committing, args=(stop,), daemon=True).start()
    try:
        result = subprocess.run(cmd, cwd=JOBS)
    finally:
        stop.set()
        volume.commit()
    return result.returncode


@app.local_entrypoint()
def main(
    binary: str,
    tasks: int = 20,
    attempts: int = 1,
    concurrent: int = 5,
    dataset: str = "terminal-bench/terminal-bench@latest",
    model: str = "deepseek/deepseek-flash",
    task: str = "",
    resume: str = "",
):
    src = Path(binary).expanduser()
    files = [src] if src.is_file() else sorted(src.glob("chanto-*"))
    binaries = {f.name: f.read_bytes() for f in files}
    if not binaries:
        raise SystemExit(f"no chanto builds in {src}")
    if resume:
        args = ["job", "resume", "-p", f"jobs/{resume}"]
    else:
        source = ["-t", task] if task else ["-d", dataset, "-l", str(tasks)]
        args = [
            "run", *source, "-k", str(attempts), "-n", str(concurrent),
            "-a", "bench.terminal_bench.chanto_agent:Chanto", "-m", model,
            "--ae", "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}", "-e", "modal",
        ]
    # Spawned, not awaited: the job keeps running when this machine sleeps or
    # loses its connection (an error while waiting would stop the app).
    call = run.spawn(args, binaries)
    print(f"started {call.object_id}; follow it in the Modal dashboard")

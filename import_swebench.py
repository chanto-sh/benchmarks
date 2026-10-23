#!/usr/bin/env python3
"""Import and validate a deterministic, Docker-free SWE-bench sample.

`--dataset lite` (the default) is SWE-bench Lite; `--dataset verified` is
SWE-bench Verified, the human-validated 500-instance set. Both are imported
from Hugging Face and validated the same way: the base commit must fail the
selected tests and the gold patch must pass them."""
import argparse
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
CACHE = Path.home() / '.cache/chanto-bench'
REPOS = {'pytest-dev/pytest', 'psf/requests', 'pallets/flask', 'pylint-dev/pylint'}
DATASETS = {
    'lite': ('princeton-nlp/SWE-bench_Lite', 300),
    'verified': ('princeton-nlp/SWE-bench_Verified', 500),
}


def priority():
    return [] if hasattr(os, 'getpriority') and os.getpriority(os.PRIO_PROCESS, 0) >= 19 else ['nice', '-n', '19']


def run(cmd, cwd=None, timeout=600):
    # Kill descendants too, including test subprocesses and package builds.
    from run import run_check
    result = run_check([*priority(), *map(str, cmd)], cwd, dict(os.environ), timeout)
    if result.returncode:
        raise RuntimeError(f'exit {result.returncode}: {result.stdout[-2000:]}{result.stderr[-2000:]}')
    return result


def dataset(name):
    path = CACHE / f'swebench-{name}.json'
    if not path.exists():
        rows = []
        for offset in range(0, DATASETS[name][1], 100):
            url = (f'https://datasets-server.huggingface.co/rows?dataset={DATASETS[name][0]}'
                   f'&config=default&split=test&offset={offset}&length=100')
            with urllib.request.urlopen(url, timeout=60) as response:
                rows.extend(item['row'] for item in json.load(response)['rows'])
        if len(rows) != DATASETS[name][1]:
            raise RuntimeError(f'Expected the {DATASETS[name][1]}-instance {name} split')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rows))
    return json.loads(path.read_text())


def setup(task, python):
    meta = json.loads((task / 'instance.json').read_text())
    repo = CACHE / 'repos' / meta['repo'].replace('/', '__')
    repo.parent.mkdir(parents=True, exist_ok=True)
    if not repo.exists():
        run(['git', 'clone', '--bare', 'https://github.com/' + meta['repo'] + '.git', repo])
    marker = Path('.gitkeep')
    if marker.exists():
        marker.unlink()
    run(['git', 'clone', '--quiet', '--shared', repo, '.'])
    run(['git', 'checkout', '--quiet', meta['base_commit']])
    run([python, '-m', 'venv', '.venv'])
    py = Path.cwd() / '.venv/bin/python'
    run([py, '-m', 'pip', 'install', 'pip<25', 'setuptools<70', 'wheel'])
    deps = ['pytest==7.4.4', 'py', 'packaging', 'tomli', 'six', 'attrs', 'hypothesis==6.99.13', 'mock']
    if meta['repo'] == 'pytest-dev/pytest':
        deps += ['setuptools-scm<8', 'xmlschema<3', 'pexpect', 'nose', 'argcomplete', 'requests']
    elif meta['repo'] == 'pallets/flask':
        deps += ['Werkzeug<2.4', 'Jinja2<3.2', 'itsdangerous<2.2', 'click<8.2', 'blinker', 'python-dotenv']
    elif meta['repo'] == 'pylint-dev/pylint':
        deps += ['astroid>=2.11,<2.16', 'pytest-benchmark', 'pytest-timeout', 'gitpython', 'testutils', 'toml', 'typing-extensions']
    run([py, '-m', 'pip', 'install', *deps])
    run([py, '-m', 'pip', 'install', '--no-build-isolation', '-e', '.'])
    # Start a fresh history at the base snapshot: the clone's later commits
    # include the upstream fix, one `git log --all` away.
    shutil.rmtree('.git')
    run(['git', 'init', '--quiet'])
    with open('.git/info/exclude', 'a') as f:
        f.write('\n.venv/\n.swe-results.xml\n')
    run(['git', 'add', '-A'])
    run(['git', '-c', 'user.email=b@b', '-c', 'user.name=bench', 'commit', '--quiet', '-m', 'base'])


def base_rev():
    out = subprocess.run(['git', 'rev-list', '--max-parents=0', 'HEAD'], capture_output=True, text=True, check=True)
    return out.stdout.split()[-1]


def check(task):
    meta = json.loads((task / 'instance.json').read_text())
    # Restore every patched test/fixture from the base, including deleted files.
    patch = (task / 'test.patch').read_text()
    base = base_rev()
    roots = {t.split('/', 1)[0] for t in meta['FAIL_TO_PASS'] + meta['PASS_TO_PASS'] if '/' in t}
    for root in roots:
        run(['git', 'restore', '--source=' + base, '--worktree', '--', root])
    paths = re.findall(r'^diff --git a/(.*?) b/.*$', patch, re.M)
    for path in paths:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
        subprocess.run(['git', 'restore', '--source=' + base, '--', path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run(['git', 'apply', task / 'test.patch'])
    # The upstream parser also recorded progress-bar fragments as tests.
    ids = [t for t in meta['FAIL_TO_PASS'] + meta['PASS_TO_PASS']
           if not re.fullmatch(r'\[(?:[0-9]+%\])?-*', t)]
    tests = list(dict.fromkeys(t.split('[', 1)[0] for t in ids))
    if not tests:
        raise RuntimeError('No tests')
    # Empty, skipped, or collection-error runs never count as solved.
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               PATH=str(Path.cwd() / '.venv/bin') + os.pathsep + os.environ['PATH'],
               VIRTUAL_ENV=str(Path.cwd() / '.venv'),
               PYLINTHOME=str(Path.cwd() / '.venv/pylint-cache'))
    plugins = ['-p', 'pytester'] if meta['repo'] == 'pytest-dev/pytest' else []
    result = subprocess.run([*priority(), '.venv/bin/python', '-m', 'pytest', '-o', 'addopts=',
                             '-q', '--junitxml=.swe-results.xml', *plugins, *tests],
                            env=env)
    if result.returncode:
        sys.exit(result.returncode)
    cases = ET.parse('.swe-results.xml').findall('.//testcase')
    if len(cases) < len(tests) or any(c.find(tag) is not None for c in cases for tag in ('skipped', 'failure', 'error')):
        sys.exit(1)


def make_task(row, dest, python, name):
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'files').mkdir(exist_ok=True)
    (dest / 'files/.gitkeep').touch()
    meta = {'dataset': name}
    meta.update({k: row[k] for k in ('instance_id', 'repo', 'base_commit', 'environment_setup_commit')})
    for k in ('FAIL_TO_PASS', 'PASS_TO_PASS'):
        meta[k] = json.loads(row[k])
    (dest / 'instance.json').write_text(json.dumps(meta, indent=2) + '\n')
    (dest / 'test.patch').write_text(row['test_patch'])
    (dest / 'prompt.txt').write_text(row['problem_statement'].rstrip() + '\n\nFix the issue in this repository. Run the relevant tests.\n')
    import shlex
    runtime = (str(Path(__file__).resolve()) if dest.parent != ROOT / 'tasks'
               else '$(cd "$(dirname "$0")/../.." && pwd)/import_swebench.py')
    for name, mode in [('setup', '--setup'), ('check', '--check')]:
        (dest / (name + '.sh')).write_text('#!/bin/bash\nset -eu\n' +
            f'exec python3 "{runtime}" '
            f'{mode} "$(dirname "$0")" --python {shlex.quote(python)}\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset', choices=sorted(DATASETS), default='lite')
    ap.add_argument('--count', type=int, default=25)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--python', help='override the automatically selected repository interpreter')
    ap.add_argument('--dest', type=Path, default=ROOT / 'tasks')
    ap.add_argument('--ids', type=Path, help='revalidate exactly the IDs in a JSON list')
    ap.add_argument('--validation-report', type=Path,
                    help='default: swebench-<dataset>-validation.json in the cache')
    ap.add_argument('--setup', type=Path)
    ap.add_argument('--check', type=Path)
    args = ap.parse_args()
    if args.setup:
        setup(args.setup.resolve(), args.python or sys.executable)
        return
    if args.check:
        check(args.check.resolve())
        return
    suffix = '' if args.dataset == 'lite' else '-' + args.dataset
    selection = ROOT / f'swebench{suffix}-selection.json'
    report_path = args.validation_report or CACHE / f'swebench{suffix}-validation.json'
    rows = [r for r in dataset(args.dataset) if r['repo'] in REPOS]
    if args.dataset == 'lite':
        # The generic requests environment only resolved this instance when the
        # Lite sample was validated; Verified tries all of them.
        rows = [r for r in rows if r['repo'] != 'psf/requests' or r['instance_id'] == 'psf__requests-3362']
    rows.sort(key=lambda r: r['instance_id'])
    random.Random(args.seed).shuffle(rows)
    if args.ids:
        ids = json.loads(args.ids.read_text())
        rows = sorted((r for r in rows if r['instance_id'] in ids), key=lambda r: ids.index(r['instance_id']))
        if len(rows) != len(ids):
            ap.error('Some requested IDs are missing or unsupported')
        args.count = len(ids)
    CACHE.mkdir(parents=True, exist_ok=True)
    report = []
    kept = []
    for row in rows:
        if len(kept) >= args.count:
            break
        task = args.dest.resolve() / ('swe-' + row['instance_id'])
        python = args.python or ('python3.11' if row['instance_id'] == 'pallets__flask-4992' and shutil.which('python3.11')
                                  else 'python3.9' if shutil.which('python3.9') else sys.executable)
        make_task(row, task, python, args.dataset)
        start = time.monotonic()
        status = 'rejected'
        try:
            with tempfile.TemporaryDirectory(prefix='swe-', dir=CACHE) as wd:
                run(['bash', task / 'setup.sh'], cwd=wd, timeout=600)
                remaining = lambda: max(1, 600 - (time.monotonic() - start))
                from run import run_check
                base = run_check(['nice', '-n', '19', 'bash', str(task / 'check.sh')], wd, dict(os.environ), min(120, remaining()))
                (CACHE / (row['instance_id'] + '-base.log')).write_text(base.stdout + base.stderr)
                if base.returncode not in (1, 3) or not any(s in base.stdout for s in ('failed', 'INTERNALERROR')):
                    raise RuntimeError('Base did not produce a test failure')
                gold = Path(wd) / 'gold.patch'
                gold.write_text(row['patch'])
                run(['git', 'apply', gold], cwd=wd, timeout=remaining())
                result = run_check(['nice', '-n', '19', 'bash', str(task / 'check.sh')], wd, dict(os.environ), min(120, remaining()))
                (CACHE / (row['instance_id'] + '-gold.log')).write_text(result.stdout + result.stderr)
                if result.returncode or time.monotonic() - start > 600:
                    raise RuntimeError('Gold failed or exceeded ten minutes')
                status = 'base FAIL / gold PASS'
                kept.append(row['instance_id'])
        except Exception as exc:
            status = str(exc).replace('\n', ' ')[-350:]
            shutil.rmtree(task)
        report.append({'instance_id': row['instance_id'], 'result': status, 'seconds': round(time.monotonic() - start, 1)})
        print(f"{row['instance_id']}: {status} ({report[-1]['seconds']}s)", flush=True)
        if not args.ids:
            selection.write_text(json.dumps(kept, indent=2) + '\n')
        report_path.write_text(json.dumps(report, indent=2) + '\n')
    print('\n| instance | validation | seconds |\n|---|---|---|')
    for item in report:
        print(f"| {item['instance_id']} | {item['result']} | {item['seconds']} |")
    print(f'Kept {len(kept)} / {len(report)} candidates')
    if args.ids and len(kept) != args.count:
        sys.exit(1)


if __name__ == '__main__':
    main()

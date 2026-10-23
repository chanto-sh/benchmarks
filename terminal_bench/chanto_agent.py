"""Harbor integration for chanto, for Terminal-Bench and other Harbor datasets.

Harbor installs chanto inside each task container and runs it once in print
mode on the task's instruction, the way it runs Claude Code or Goose.

    harbor run -d terminal-bench/terminal-bench@latest \\
        -a bench.terminal_bench.chanto_agent:Chanto \\
        -m deepseek/deepseek-flash \\
        --ak binary=/path/to/linux-builds \\
        --ae DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY"

The model is any spec chanto accepts (`provider/model`, resolved by chanto's
own provider catalog); pass that provider's key with `--ae`. Options (`--ak`):

- `binary` (required): static Linux builds of chanto to upload, since the
  repository's releases aren't public. Either one binary, or a directory with
  `chanto-x86_64` and/or `chanto-aarch64`; the one matching the container's
  architecture is installed.
- `chanto_args`: extra chanto flags, e.g. `--verify`.
"""

import json
import shlex
from pathlib import Path
from typing import override

from harbor.agents.installed.base import BaseInstalledAgent, with_prompt_template
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

BIN = "$HOME/.local/bin/chanto"
LOGS = "/logs/agent"


class Chanto(BaseInstalledAgent):
    def __init__(self, *args, binary: str | None = None, chanto_args: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._binary = binary
        self._chanto_args = chanto_args

    @staticmethod
    @override
    def name() -> str:
        return "chanto"

    @override
    def version(self) -> str:
        return self._version or "local"

    @override
    def get_version_command(self) -> str | None:
        return f"{BIN} --version"

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        if not self._binary:
            raise ValueError("chanto needs --ak binary=<linux build or directory of builds>")
        src = Path(self._binary).expanduser()
        builds = [src] if src.is_file() else sorted(src.glob("chanto-*"))
        if not builds:
            raise ValueError(f"no chanto builds in {src}")
        # chanto trusts the system's certificate store; slim images have none.
        await self.ensure_system_dependencies(environment, ("ca_certificates", "git"))
        for b in builds:
            await environment.upload_file(b, f"/tmp/{b.name}")
        await self.exec_as_root(
            environment,
            command=(
                "set -eu; arch=$(uname -m); "
                'case "$arch" in arm64) arch=aarch64;; amd64) arch=x86_64;; esac; '
                'src=/tmp/chanto-$arch; [ -f "$src" ] || src=/tmp/chanto; '
                'install -m 755 "$src" /usr/local/bin/chanto'
            ),
        )
        await self.exec_as_agent(
            environment, command=f'mkdir -p "$HOME/.local/bin" && ln -sf /usr/local/bin/chanto {BIN} && {BIN} --version'
        )

    @with_prompt_template
    @override
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        if not self.model_name:
            raise ValueError("chanto needs a model: -m provider/model")
        env = {
            # Sessions land in the trial's logs, so they're kept with the result.
            "CHANTO_HOME": f"{LOGS}/chanto-home",
            "CHANTO_NO_UPDATE_CHECK": "1",
            **self.resolve_env_vars(),
        }
        command = (
            f"cd \"${{HARBOR_WORKDIR:-$PWD}}\" && {BIN} -p --mode bypassPermissions "
            f"--model {shlex.quote(self.model_name)} --output-format json "
            # Print mode reads piped stdin as extra input; Harbor leaves it open.
            f"{self._chanto_args} {shlex.quote(instruction)} < /dev/null "
            f"> {LOGS}/chanto.json 2> {LOGS}/chanto.err"
        )
        await self.exec_as_agent(environment, command=command, env=env)

    @override
    def populate_context_post_run(self, context: AgentContext) -> None:
        path = Path(self.logs_dir) / "chanto.json"
        try:
            result = json.loads(path.read_text())
        except (OSError, ValueError):
            return
        usage = result.get("usage") or {}
        context.n_input_tokens = usage.get("input_tokens") or 0
        context.n_output_tokens = usage.get("output_tokens") or 0
        if usage.get("cached_tokens") is not None:
            context.n_cache_tokens = usage["cached_tokens"]
        if result.get("total_cost_usd") is not None:
            context.cost_usd = result["total_cost_usd"]

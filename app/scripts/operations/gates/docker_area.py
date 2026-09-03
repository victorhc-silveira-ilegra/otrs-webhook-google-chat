from __future__ import annotations

from operations.gates.common import (
    DOCKER_DIR,
    REPO_ROOT,
    require_binary,
    run_cmd,
    stage_ok,
)

_DOCKERFILES = (
    DOCKER_DIR / "notifier" / "Dockerfile",
    DOCKER_DIR / "otrs" / "Dockerfile",
)
_REQUIRED = (
    DOCKER_DIR / "docker-compose.yml",
    DOCKER_DIR / "notifier" / "Dockerfile",
    DOCKER_DIR / "otrs" / "Dockerfile",
    DOCKER_DIR / "mariadb" / "init.sql",
    DOCKER_DIR / "scripts" / "docker-smoke.sh",
    DOCKER_DIR / "scripts" / "docker-health.sh",
)


def _compose_cmd() -> list[str]:
    env_file = REPO_ROOT / ".env"
    if not env_file.is_file():
        env_file = REPO_ROOT / ".env.example"
    return [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(DOCKER_DIR / "docker-compose.yml"),
        "--project-directory",
        str(DOCKER_DIR),
    ]


def lint() -> None:
    hadolint = require_binary("hadolint")
    config = DOCKER_DIR / ".hadolint.yaml"
    for dockerfile in _DOCKERFILES:
        command = [hadolint]
        if config.is_file():
            command.extend(["--config", str(config)])
        command.append(str(dockerfile))
        run_cmd(
            command,
            description=f"Hadolint {dockerfile.relative_to(REPO_ROOT)}",
        )
    stage_ok("Lint Docker concluido")


def security() -> None:
    trivy = require_binary("trivy")
    ignorefile = DOCKER_DIR / ".trivyignore"
    ignore_args: list[str] = []
    if ignorefile.is_file():
        ignore_args = ["--ignorefile", str(ignorefile)]
    run_cmd(
        [
            trivy,
            "config",
            "--exit-code",
            "1",
            "--severity",
            "HIGH,CRITICAL",
            *ignore_args,
            str(DOCKER_DIR),
        ],
        description="Trivy config infra/docker",
    )
    run_cmd(
        [
            trivy,
            "fs",
            "--exit-code",
            "1",
            "--severity",
            "HIGH,CRITICAL",
            "--scanners",
            "vuln,secret",
            *ignore_args,
            str(DOCKER_DIR),
        ],
        description="Trivy fs infra/docker",
    )
    stage_ok("Seguranca Docker concluida")


def test() -> None:
    require_binary("docker")
    run_cmd(
        [*_compose_cmd(), "config", "--quiet"],
        description="docker compose config --quiet",
    )
    stage_ok("Testes Docker concluidos")


def validate() -> None:
    missing = [path for path in _REQUIRED if not path.is_file()]
    if missing:
        print("\n[ERRO] Arquivos Docker obrigatorios ausentes:")
        for path in missing:
            print(f"  - {path.relative_to(REPO_ROOT)}")
        raise SystemExit(1)
    require_binary("docker")
    run_cmd(
        [*_compose_cmd(), "config", "--quiet"],
        description="docker compose config --quiet",
    )
    stage_ok("Validate Docker concluido")


def build() -> None:
    require_binary("docker")
    run_cmd(
        [
            "docker",
            "build",
            "-f",
            str(DOCKER_DIR / "notifier" / "Dockerfile"),
            "-t",
            "otrs-notifier:ci",
            str(REPO_ROOT),
        ],
        description="docker build notifier",
    )
    stage_ok("Build Docker (notifier) concluido")

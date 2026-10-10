#!/usr/bin/env python3
"""ParkMate local ops: env checks, health probes, wait loops, and Postgres dumps."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
BACKUP_DIR = REPO_ROOT / "devops" / "backups"

REQUIRED_KEYS = (
    "APP_ENV",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "INITIAL_ADMIN_USERNAME",
    "INITIAL_ADMIN_PASSWORD",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_URL",
    "BACKEND_URL",
)

COMPOSE_SERVICES = (
    "postgres",
    "redis",
    "backend",
    "frontend",
    "ml-worker",
    "nginx",
)


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def merged_env() -> dict[str, str]:
    env = load_env_file(ENV_EXAMPLE)
    env.update(load_env_file(ENV_FILE))
    env.update(os.environ)
    return env


def parse_host_port(url_or_host: str, default_port: int) -> tuple[str, int]:
    if "://" in url_or_host:
        parsed = urlparse(url_or_host)
        host = parsed.hostname or "localhost"
        port = parsed.port or default_port
        return host, port
    if ":" in url_or_host:
        host, port_text = url_or_host.rsplit(":", 1)
        return host, int(port_text)
    return url_or_host, default_port


def tcp_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_json(url: str, timeout: float = 3.0) -> tuple[int, dict]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body) if body else {}
            return response.status, payload
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": str(exc)}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return 0, {"error": str(exc)}


def compose_cmd(args: Iterable[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def cmd_validate_env() -> int:
    example = load_env_file(ENV_EXAMPLE)
    local = load_env_file(ENV_FILE)
    missing_example = [key for key in REQUIRED_KEYS if key not in example]
    missing_local = [key for key in REQUIRED_KEYS if key not in local and key not in example]

    print(f"repo: {REPO_ROOT}")
    print(f".env.example: {'found' if ENV_EXAMPLE.exists() else 'missing'}")
    print(f".env: {'found' if ENV_FILE.exists() else 'missing (using example defaults)'}")

    if missing_example:
        print("missing keys in .env.example:")
        for key in missing_example:
            print(f"  - {key}")
        return 1

    if missing_local and not ENV_FILE.exists():
        print("warning: copy .env.example to .env before bringing the stack up")

    values = merged_env()
    missing_secrets = [
        key for key in (
            "POSTGRES_PASSWORD",
            "JWT_SECRET_KEY",
            "INITIAL_ADMIN_USERNAME",
            "INITIAL_ADMIN_PASSWORD",
        ) if not values.get(key)
    ]
    if missing_secrets:
        print("required secrets are missing or blank:")
        for key in missing_secrets:
            print(f"  - {key}")
        return 1

    database_url = values.get("DATABASE_URL", "")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        print("DATABASE_URL must use a PostgreSQL URL")
        return 1

    print("env looks valid for ParkMate Compose")
    return 0


def cmd_init_env() -> int:
    if ENV_FILE.exists():
        print(f"{ENV_FILE} already exists; refusing to overwrite it")
        return 1
    if not ENV_EXAMPLE.is_file():
        print(f"{ENV_EXAMPLE} is missing")
        return 1

    lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    generated = {
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        "JWT_SECRET_KEY": secrets.token_hex(32),
        "INITIAL_ADMIN_USERNAME": "admin",
        "INITIAL_ADMIN_PASSWORD": secrets.token_urlsafe(32),
    }
    updated_lines = []
    for line in lines:
        key, separator, _ = line.partition("=")
        if separator and key in generated:
            line = f"{key}={generated[key]}"
        updated_lines.append(line)

    ENV_FILE.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    ENV_FILE.chmod(0o600)
    print(f"created {ENV_FILE} with fresh local secrets; do not commit this file")
    return 0


def cmd_health(base_url: str) -> int:
    health_url = f"{base_url.rstrip('/')}/health"
    ready_url = f"{base_url.rstrip('/')}/ready"
    health_status, health_body = http_json(health_url)
    ready_status, ready_body = http_json(ready_url)

    print(json.dumps(
        {
            "health": {"status_code": health_status, "body": health_body},
            "ready": {"status_code": ready_status, "body": ready_body},
        },
        indent=2,
    ))

    if health_status != 200:
        print("health check failed")
        return 1
    if ready_status != 200:
        print("readiness check failed")
        return 1
    return 0


def remap_compose_host(host: str) -> str:
    if host in {"postgres", "redis", "backend", "frontend", "nginx"}:
        return "127.0.0.1"
    return host


def cmd_wait(timeout_seconds: int) -> int:
    env = merged_env()
    redis_host, redis_port = parse_host_port(
        env.get("REDIS_URL") or env.get("REDIS_HOST", "127.0.0.1"),
        int(env.get("REDIS_PORT", "6379")),
    )
    pg_host, pg_port = parse_host_port(
        env.get("DATABASE_URL", "postgresql://127.0.0.1:5432/parkmate"),
        5432,
    )
    pg_host = remap_compose_host(pg_host)
    redis_host = remap_compose_host(redis_host)

    deadline = time.time() + timeout_seconds
    targets = {
        "postgres": (pg_host, pg_port),
        "redis": (redis_host, redis_port),
        "api": ("127.0.0.1", 8000),
        "gateway": ("127.0.0.1", 80),
    }

    while time.time() < deadline:
        pending = [
            name
            for name, (host, port) in targets.items()
            if not tcp_open(host, port)
        ]
        if not pending:
            print("postgres, redis, api, and nginx gateway are accepting connections")
            return 0
        print(f"waiting on: {', '.join(pending)}")
        time.sleep(2)

    print(f"timed out after {timeout_seconds}s")
    return 1


def cmd_status() -> int:
    result = compose_cmd(["ps", "--format", "json"])
    if result.returncode != 0:
        print(result.stderr.strip() or "docker compose ps failed")
        return result.returncode

    rows = []
    stdout = result.stdout.strip()
    if stdout.startswith("["):
        rows = json.loads(stdout)
    elif stdout:
        for line in stdout.splitlines():
            rows.append(json.loads(line))

    found = {row.get("Service") or row.get("Name") for row in rows}
    print(f"{'service':<14} {'state':<12} {'health'}")
    for service in COMPOSE_SERVICES:
        match = next(
            (
                row
                for row in rows
                if service in str(row.get("Service", ""))
                or service in str(row.get("Name", ""))
            ),
            None,
        )
        if not match:
            print(f"{service:<14} {'missing':<12} -")
            continue
        state = match.get("State") or match.get("Status") or "unknown"
        health = match.get("Health") or "-"
        print(f"{service:<14} {str(state):<12} {health}")

    missing = [service for service in COMPOSE_SERVICES if service not in found]
    if missing and not rows:
        print("stack does not appear to be running")
        return 1
    return 0


def cmd_backup() -> int:
    env = merged_env()
    user = env.get("POSTGRES_USER", "parkmate")
    database = env.get("POSTGRES_DB", "parkmate")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outfile = BACKUP_DIR / f"parkmate-{database}-{stamp}.sql"

    dump = compose_cmd(
        [
            "exec",
            "-T",
            "postgres",
            "pg_dump",
            "-U",
            user,
            "-d",
            database,
        ]
    )
    if dump.returncode != 0:
        print(dump.stderr.strip() or "pg_dump failed; is the stack up?")
        return dump.returncode

    outfile.write_text(dump.stdout, encoding="utf-8")
    print(f"wrote {outfile} ({outfile.stat().st_size} bytes)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ParkMate DevOps helper for local Compose operations",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-env", help="create a local .env with fresh secrets")
    sub.add_parser("validate-env", help="check required ParkMate env keys")
    health = sub.add_parser("health", help="probe API /health and /ready")
    health.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="API base URL (use http://127.0.0.1 for nginx gateway + /health)",
    )
    wait = sub.add_parser("wait", help="wait until local ports are open")
    wait.add_argument("--timeout", type=int, default=90)
    sub.add_parser("status", help="show Compose service health")
    sub.add_parser("backup-db", help="dump Postgres from the postgres service")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init-env":
        return cmd_init_env()
    if args.command == "validate-env":
        return cmd_validate_env()
    if args.command == "health":
        return cmd_health(args.base_url)
    if args.command == "wait":
        return cmd_wait(args.timeout)
    if args.command == "status":
        return cmd_status()
    if args.command == "backup-db":
        return cmd_backup()
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import argparse
import atexit
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

from automessage import __version__
from automessage.config import get_settings


def _run_alembic_upgrade(database_url: str) -> None:
    """Apply migrations when Alembic config is present (dev / source tree)."""
    candidates = [
        Path(__file__).resolve().parent.parent / "alembic.ini",
        Path.cwd() / "alembic.ini",
    ]
    alembic_ini = next((p for p in candidates if p.exists()), None)
    if alembic_ini is None:
        return
    try:
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(alembic_ini))
        cfg.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(cfg, "head")
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("automessage").warning("Alembic upgrade skipped: %s", exc)


def _open_browser_later(url: str, delay: float = 1.2) -> None:
    def _open() -> None:
        time.sleep(delay)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


def _write_pid_file(pid_path: Path, port: int) -> None:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(f"{os.getpid()}\n{port}\n", encoding="utf-8")


def _clear_pid_file(pid_path: Path) -> None:
    try:
        pid_path.unlink(missing_ok=True)
    except OSError:
        pass


def _read_pid_file(pid_path: Path) -> tuple[int, int | None] | None:
    if not pid_path.exists():
        return None
    try:
        lines = pid_path.read_text(encoding="utf-8").strip().splitlines()
        pid = int(lines[0])
        port = int(lines[1]) if len(lines) > 1 else None
        return pid, port
    except (ValueError, OSError):
        return None


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = (result.stdout or "").strip()
        return bool(out) and "No tasks are running" not in out and str(pid) in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _kill_process_tree(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
        )
        return
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def _find_pids_on_port(port: int) -> list[int]:
    """Best-effort lookup when the pid file is missing (Windows / Unix)."""
    pids: list[int] = []
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            needle = f":{port} "
            for line in result.stdout.splitlines():
                if needle not in line or "LISTENING" not in line.upper():
                    continue
                parts = line.split()
                if not parts:
                    continue
                try:
                    pid = int(parts[-1])
                except ValueError:
                    continue
                if pid > 0 and pid not in pids:
                    pids.append(pid)
            return pids

        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                pid = int(line)
            except ValueError:
                continue
            if pid > 0 and pid not in pids:
                pids.append(pid)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return pids
    return pids


def cmd_start(args: argparse.Namespace) -> int:
    # Allow `automessage start default` to flip mode before settings are read.
    if getattr(args, "profile", None) == "default":
        os.environ["AUTOMESSAGE_DEFAULT_USER_MODE"] = "true"
        get_settings.cache_clear()

    settings = get_settings()
    if args.host:
        settings.host = args.host
    if args.port:
        settings.port = args.port
    if args.no_browser:
        settings.open_browser = False
    if getattr(args, "profile", None) == "default":
        settings.default_user_mode = True

    settings.ensure_dirs()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    log = logging.getLogger("automessage")

    existing = _read_pid_file(settings.pid_path)
    if existing and _pid_is_running(existing[0]):
        log.error(
            "AutoMessage already running (pid %s). Stop it with: automessage stop",
            existing[0],
        )
        return 1

    _write_pid_file(settings.pid_path, settings.port)
    atexit.register(_clear_pid_file, settings.pid_path)

    _run_alembic_upgrade(settings.database_url)

    url = f"http://{settings.host}:{settings.port}"
    log.info("AutoMessage v%s starting at %s", __version__, url)
    log.info("Database: %s", settings.resolved_db_path)
    if settings.default_user_mode:
        from automessage.auth.sessions import (
            DEFAULT_USER_EMAIL,
            DEFAULT_USER_PASSWORD,
        )

        log.info(
            "Default user mode — auto sign-in as %s (password: %s)",
            DEFAULT_USER_EMAIL,
            DEFAULT_USER_PASSWORD,
        )
    else:
        log.info("Auth required — open the app to sign up or sign in")

    if settings.open_browser and settings.host in {"127.0.0.1", "localhost", "0.0.0.0"}:
        _open_browser_later(f"http://127.0.0.1:{settings.port}")

    try:
        uvicorn.run(
            "automessage.main:create_app",
            factory=True,
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level.lower(),
            reload=args.reload,
        )
    finally:
        _clear_pid_file(settings.pid_path)
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    settings = get_settings()
    if args.port:
        settings.port = args.port

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    log = logging.getLogger("automessage")

    targets: list[int] = []
    recorded = _read_pid_file(settings.pid_path)
    if recorded and _pid_is_running(recorded[0]):
        targets.append(recorded[0])

    port = args.port or (recorded[1] if recorded else None) or settings.port
    for pid in _find_pids_on_port(port):
        if pid not in targets and _pid_is_running(pid):
            targets.append(pid)

    if not targets:
        if recorded and not _pid_is_running(recorded[0]):
            _clear_pid_file(settings.pid_path)
        log.info("AutoMessage is not running")
        return 0

    for pid in targets:
        log.info("Stopping AutoMessage (pid %s)…", pid)
        _kill_process_tree(pid)

    # Wait briefly for processes to exit
    deadline = time.time() + 5
    while time.time() < deadline and any(_pid_is_running(pid) for pid in targets):
        time.sleep(0.15)

    still = [pid for pid in targets if _pid_is_running(pid)]
    _clear_pid_file(settings.pid_path)
    if still:
        log.error("Failed to stop process(es): %s", ", ".join(str(p) for p in still))
        return 1

    log.info("AutoMessage stopped")
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="automessage",
        description="AutoMessage — local-first DM automation",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start", help="Start the API server and open the UI")
    start.add_argument(
        "profile",
        nargs="?",
        choices=["default"],
        default=None,
        help="Use 'default' to auto sign-in as the seeded local default user",
    )
    start.add_argument("--host", default=None, help="Bind host (default: 127.0.0.1)")
    start.add_argument("--port", type=int, default=None, help="Bind port (default: 8741)")
    start.add_argument("--no-browser", action="store_true", help="Do not open a browser")
    start.add_argument("--reload", action="store_true", help="Enable auto-reload (dev)")
    start.set_defaults(func=cmd_start)

    stop = sub.add_parser("stop", help="Stop the running AutoMessage server")
    stop.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to stop if the pid file is missing (default: 8741)",
    )
    stop.set_defaults(func=cmd_stop)

    ver = sub.add_parser("version", help="Print version")
    ver.set_defaults(func=cmd_version)

    return parser


_KNOWN_COMMANDS = {"start", "stop", "version", "-h", "--help", "--version"}


def main(argv: list[str] | None = None) -> None:
    raw = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not raw:
        raw = ["start"]
    elif raw[0] not in _KNOWN_COMMANDS and not raw[0].startswith("-"):
        pass
    elif raw[0] not in _KNOWN_COMMANDS:
        if raw[0] == "--version":
            print(__version__)
            sys.exit(0)
        raw = ["start", *raw]

    args = parser.parse_args(raw)
    if getattr(args, "version", False) and not getattr(args, "command", None):
        print(__version__)
        sys.exit(0)
    if not getattr(args, "command", None):
        args = parser.parse_args(["start"])
    code = args.func(args)
    sys.exit(code or 0)


if __name__ == "__main__":
    main()

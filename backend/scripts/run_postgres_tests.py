"""Run tests against a private local PostgreSQL cluster, then stop it."""

import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-bin", type=Path, required=True)
    args = parser.parse_args()
    backend = Path(__file__).resolve().parents[1]
    root = backend / ".test-postgres"
    root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="cluster-", dir=root)).resolve()
    if not directory.is_relative_to(root.resolve()):
        raise RuntimeError("Test cluster path escaped its workspace root")
    data = directory / "data"
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def run(binary, *arguments):
        executable = args.postgres_bin / (binary + (".exe" if os.name == "nt" else ""))
        # pg_ctl's server inherits handles on Windows. Files avoid waiting for
        # the long-lived server to close a captured stdout/stderr pipe.
        output = directory / "command.log"
        with output.open("w", encoding="utf-8") as stream:
            result = subprocess.run(
                [str(executable), *map(str, arguments)],
                stdout=stream,
                stderr=subprocess.STDOUT,
                creationflags=flags,
                check=False,
            )
        print(output.read_text(encoding="utf-8", errors="replace"), end="", flush=True)
        result.check_returncode()

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    started = False
    try:
        run(
            "initdb",
            "-D",
            data,
            "-U",
            "postgres",
            "-A",
            "trust",
            "--encoding=UTF8",
            "--locale=C",
        )
        run(
            "pg_ctl",
            "-D",
            data,
            "-l",
            directory / "postgres.log",
            "-o",
            f"-h 127.0.0.1 -p {port}",
            "-w",
            "start",
        )
        started = True
        run(
            "createdb",
            "-h",
            "127.0.0.1",
            "-p",
            port,
            "-U",
            "postgres",
            "second_brain_test",
        )
        environment = os.environ.copy()
        environment["TEST_POSTGRES_URL"] = (
            f"postgresql+psycopg2://postgres@127.0.0.1:{port}/second_brain_test"
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-q",
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=xml",
            ],
            cwd=backend,
            env=environment,
            creationflags=flags,
            capture_output=True,
            text=True,
            errors="replace",
        )
        print(result.stdout, end="", flush=True)
        print(result.stderr, end="", file=sys.stderr, flush=True)
        return result.returncode
    finally:
        if started:
            run("pg_ctl", "-D", data, "-m", "fast", "-w", "stop")
        # Only remove this newly created cluster after the server has stopped.
        if directory.is_relative_to(root.resolve()):
            shutil.rmtree(directory)


if __name__ == "__main__":
    sys.exit(main())

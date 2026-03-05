#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print(f"[dev-harness] $ {' '.join(shlex.quote(c) for c in cmd)}")
    proc = subprocess.run(cmd, cwd=ROOT, check=False)
    if proc.returncode != 0:
        sys.exit(proc.returncode)


def git_changed_files() -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []

    changed: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if path:
            changed.append(path.replace("\\", "/"))
    return changed


def changed_integration_tests(changed_files: list[str]) -> list[str]:
    tests: list[str] = []
    for path in changed_files:
        if path.startswith("tests/") and path.endswith(".rs"):
            test_name = Path(path).stem
            if test_name not in tests:
                tests.append(test_name)
    return tests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fast local coding harness for LocalAgent."
    )
    parser.add_argument(
        "--profile",
        choices=["quick", "full"],
        default="quick",
        help="quick = tight loop checks, full = CI-like checks",
    )
    parser.add_argument(
        "--changed-tests",
        action="store_true",
        help="In quick mode, run only changed integration tests from tests/*.rs (falls back to cargo test --lib if none changed).",
    )
    parser.add_argument(
        "--skip-fmt",
        action="store_true",
        help="Skip cargo fmt --check",
    )
    parser.add_argument(
        "--skip-clippy",
        action="store_true",
        help="Skip cargo clippy",
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip cargo test",
    )
    parser.add_argument(
        "--locked",
        action="store_true",
        help="Pass --locked to cargo commands",
    )
    return parser.parse_args()


def maybe_locked(args: argparse.Namespace) -> list[str]:
    return ["--locked"] if args.locked else []


def run_quick(args: argparse.Namespace) -> None:
    if not args.skip_fmt:
        run(["cargo", "fmt", "--all", "--", "--check"])

    if not args.skip_clippy:
        run(
            ["cargo", "clippy", "--all-targets", "--all-features", *maybe_locked(args), "--", "-D", "warnings"]
        )

    if args.skip_test:
        return

    if args.changed_tests:
        changed = git_changed_files()
        tests = changed_integration_tests(changed)
        if tests:
            for test in tests:
                run(["cargo", "test", *maybe_locked(args), "--test", test])
            return
        print("[dev-harness] no changed integration tests found; running cargo test --lib")
        run(["cargo", "test", *maybe_locked(args), "--lib"])
        return

    run(["cargo", "test", *maybe_locked(args), "--lib", "--tests"])


def run_full(args: argparse.Namespace) -> None:
    if not args.skip_fmt:
        run(["cargo", "fmt", "--all", "--", "--check"])

    if not args.skip_clippy:
        run(
            ["cargo", "clippy", "--workspace", "--all-targets", "--all-features", *maybe_locked(args), "--", "-D", "warnings"]
        )

    if not args.skip_test:
        run(["cargo", "test", "--workspace", *maybe_locked(args)])


def main() -> None:
    args = parse_args()
    started = time.time()
    if args.profile == "full":
        run_full(args)
    else:
        run_quick(args)
    elapsed = time.time() - started
    print(f"[dev-harness] OK ({args.profile} profile) in {elapsed:.1f}s")


if __name__ == "__main__":
    main()

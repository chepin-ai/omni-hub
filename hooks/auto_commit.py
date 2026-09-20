#!/usr/bin/env python3
"""
auto_commit.py — Automated git commit hook with debounce, safety scan, and CLI.
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock, Timer


class AutoGitHook:
    """
    Watches a directory for file changes, debounces events,
    scans for secrets, auto-commits, and optionally pushes.
    """

    # Patterns that indicate potential secrets
    SECRET_PATTERNS = [
        re.compile(r'API_KEY\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?', re.IGNORECASE),
        re.compile(r'TOKEN\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?', re.IGNORECASE),
        re.compile(r'PASSWORD\s*[=:]\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
        re.compile(r'SECRET\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?', re.IGNORECASE),
        re.compile(r'AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?[A-Z0-9]{20}["\']?', re.IGNORECASE),
        re.compile(r'AWS_SECRET_ACCESS_KEY\s*[=:]\s*["\']?[A-Za-z0-9/+=]{40}["\']?', re.IGNORECASE),
    ]

    def __init__(self, cooldown: int = 60):
        self.cooldown = cooldown
        self._last_commit_time: dict[str, float] = {}
        self._timers: dict[str, Timer] = {}
        self._lock = Lock()
        self._running = False
        self._watched_extensions = {'.py', '.lean', '.md'}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def watch_directory(self, path: str, extensions=None):
        """
        Poll-watch *path* for files matching *extensions*.
        When a file’s mtime or size changes, `on_file_change` is triggered.
        """
        if extensions is not None:
            self._watched_extensions = set(extensions)

        watch_path = Path(path).resolve()
        if not watch_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {watch_path}")

        # Verify we are inside a git repo
        if not self._is_git_repo(watch_path):
            raise RuntimeError(f"{watch_path} is not inside a git repository")

        self._running = True
        print(f"[AutoGitHook] Watching {watch_path} for {self._watched_extensions}")
        print(f"[AutoGitHook] Cooldown: {self.cooldown}s  |  Press Ctrl+C to stop")

        snapshots: dict[str, tuple[float, int]] = {}

        try:
            while self._running:
                current = self._snapshot(watch_path)
                for filepath, (mtime, size) in current.items():
                    old = snapshots.get(filepath)
                    if old is None or old != (mtime, size):
                        self.on_file_change(filepath)
                snapshots = current
                time.sleep(2)
        except KeyboardInterrupt:
            self._running = False
            print("\n[AutoGitHook] Stopped.")

    def on_file_change(self, filepath: str):
        """
        Called whenever a watched file changes.
        Debounces rapid successive events with a single timer per file.
        """
        with self._lock:
            old_timer = self._timers.get(filepath)
            if old_timer is not None:
                old_timer.cancel()

            timer = Timer(self.cooldown, self._debounced_commit, args=(filepath,))
            self._timers[filepath] = timer
            timer.start()
            print(f"[AutoGitHook] Change detected: {filepath}  (debounce {self.cooldown}s)")

    def commit_change(self, filepath: str):
        """
        Stage, safety-scan, and commit a single file.
        Returns True if a commit was created.
        """
        filepath = Path(filepath).resolve()
        if not filepath.exists():
            print(f"[AutoGitHook] File vanished: {filepath}")
            return False

        # Safety scan
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        if self._scan_for_secrets(content):
            print(f"[AutoGitHook] BLOCKED: secrets detected in {filepath.name}")
            return False

        # Build commit message
        filename = filepath.name
        energy = self._compute_energy(content)
        level = self._compute_level(content)
        message = f"auto: {filename} | E={energy} L={level}"

        # Stage the file
        repo_root = self._git_root(filepath)
        rel_path = filepath.relative_to(repo_root)
        self._git('add', str(rel_path), cwd=repo_root)

        # Only commit if there is something staged
        diff_index = self._git('diff', '--cached', '--quiet', cwd=repo_root, check=False)
        if diff_index.returncode == 0:
            print(f"[AutoGitHook] No changes to commit for {filename}")
            return False

        self._git('commit', '-m', message, cwd=repo_root)
        print(f"[AutoGitHook] Committed: {message}")
        return True

    def push_to_remote(self):
        """
        Push the current branch to its upstream remote.
        """
        repo_root = self._git_root(Path.cwd())
        result = self._git('push', cwd=repo_root, check=False, capture_output=True)
        if result.returncode == 0:
            print("[AutoGitHook] Pushed to remote.")
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore').strip()
            print(f"[AutoGitHook] Push failed: {stderr}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _debounced_commit(self, filepath: str):
        with self._lock:
            self._timers.pop(filepath, None)

        committed = self.commit_change(filepath)
        if committed:
            self.push_to_remote()

    def _snapshot(self, root: Path) -> dict[str, tuple[float, int]]:
        snap = {}
        for ext in self._watched_extensions:
            for p in root.rglob(f'*{ext}'):
                try:
                    stat = p.stat()
                    snap[str(p)] = (stat.st_mtime, stat.st_size)
                except OSError:
                    pass
        return snap

    def _scan_for_secrets(self, content: str) -> bool:
        for pattern in self.SECRET_PATTERNS:
            if pattern.search(content):
                return True
        return False

    def _compute_energy(self, content: str) -> int:
        """Rough heuristic: lines of code / 10, capped at 99."""
        loc = len(content.splitlines())
        return min(99, max(1, loc // 10))

    def _compute_level(self, content: str) -> int:
        """Rough heuristic: nesting depth based on indentation."""
        max_depth = 0
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped:
                depth = len(line) - len(stripped)
                max_depth = max(max_depth, depth // 4)
        return min(99, max(1, max_depth))

    def _is_git_repo(self, path: Path) -> bool:
        return self._git_root(path) is not None

    def _git_root(self, path: Path) -> Path | None:
        try:
            result = subprocess.run(
                ['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
                capture_output=True, text=True, check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return None

    def _git(self, *args, cwd=None, check=True, capture_output=False):
        cmd = ['git'] + list(args)
        kwargs = {'cwd': cwd, 'check': check}
        if capture_output:
            kwargs['capture_output'] = True
        return subprocess.run(cmd, **kwargs)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Auto-commit hook: watch a directory and auto-commit changes."
    )
    parser.add_argument(
        '--watch', '-w',
        metavar='PATH',
        required=True,
        help='Directory to watch'
    )
    parser.add_argument(
        '--cooldown', '-c',
        type=int,
        default=60,
        help='Debounce cooldown in seconds (default: 60)'
    )
    parser.add_argument(
        '--ext',
        nargs='+',
        default=['.py', '.lean', '.md'],
        help='File extensions to watch (default: .py .lean .md)'
    )
    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Commit only; do not push to remote'
    )

    args = parser.parse_args() if len(sys.argv) > 1 else argparse.Namespace(
        watch=".", cooldown=60, ext=['.py', '.lean', '.md'], no_push=False
    )

    hook = AutoGitHook(cooldown=args.cooldown)
    # Monkey-patch push if disabled
    if args.no_push:
        hook.push_to_remote = lambda: None

    hook.watch_directory(args.watch, extensions=args.ext)


if __name__ == '__main__':
    main()

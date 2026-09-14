from __future__ import annotations

import os
import subprocess
import threading
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence, TextIO

from .errors import AdapterStateError, ProcessExitedError, ProcessLaunchError


@dataclass(frozen=True)
class ProcessSpec:
    command: Sequence[str]
    cwd: str | os.PathLike[str] | None = None
    env_overrides: Mapping[str, str] = field(default_factory=dict)
    name: str = "runtime"


class ManagedStdioProcess:
    """Small, shell-free stdio child-process boundary owned by Hive Coder."""

    def __init__(self, spec: ProcessSpec, stderr_lines: int = 100) -> None:
        self.spec = spec
        self._stderr = deque(maxlen=stderr_lines)
        self._process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None

    @property
    def process(self) -> subprocess.Popen[str]:
        if self._process is None:
            raise AdapterStateError(f"{self.spec.name} process has not started")
        return self._process

    @property
    def stdin(self) -> TextIO:
        stream = self.process.stdin
        if stream is None:
            raise AdapterStateError(f"{self.spec.name} stdin unavailable")
        return stream

    @property
    def stdout(self) -> TextIO:
        stream = self.process.stdout
        if stream is None:
            raise AdapterStateError(f"{self.spec.name} stdout unavailable")
        return stream

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def returncode(self) -> int | None:
        return None if self._process is None else self._process.poll()

    def start(self) -> "ManagedStdioProcess":
        if self._process is not None:
            raise AdapterStateError(f"{self.spec.name} process already started")
        command = tuple(self.spec.command)
        if not command or any(not isinstance(item, str) or not item for item in command):
            raise ProcessLaunchError("process command must contain non-empty string arguments")
        cwd = None if self.spec.cwd is None else str(Path(self.spec.cwd).expanduser())
        env = os.environ.copy()
        env.update({str(key): str(value) for key, value in self.spec.env_overrides.items()})
        try:
            self._process = subprocess.Popen(
                list(command),
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="strict",
                bufsize=1,
                shell=False,
            )
        except (OSError, ValueError) as exc:
            raise ProcessLaunchError(f"failed to launch {self.spec.name}: {type(exc).__name__}") from exc
        self._stderr_thread = threading.Thread(target=self._drain_stderr, name=f"{self.spec.name}-stderr", daemon=True)
        self._stderr_thread.start()
        return self

    def _drain_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        try:
            for line in process.stderr:
                self._stderr.append(line.rstrip("\r\n"))
        except (OSError, UnicodeError):
            self._stderr.append("<stderr decode/read failure>")

    def stderr_tail(self) -> tuple[str, ...]:
        return tuple(self._stderr)

    def ensure_running(self) -> None:
        if not self.is_running:
            raise ProcessExitedError(f"{self.spec.name} exited with code {self.returncode}")

    def stop(self, grace_seconds: float = 0.5) -> None:
        process = self._process
        if process is None:
            return
        if process.stdin is not None and not process.stdin.closed:
            try:
                process.stdin.close()
            except OSError:
                pass
        if process.poll() is None:
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=grace_seconds)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=grace_seconds)
        for stream in (process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except OSError:
                    pass
        thread = self._stderr_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.2)

    def __enter__(self) -> "ManagedStdioProcess":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

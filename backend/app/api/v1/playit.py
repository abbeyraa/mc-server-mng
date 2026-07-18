import asyncio
import os
import pty
import re
import signal
import subprocess
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.playit import PlayitSettings
from app.models.user import User
from app.schemas.playit import PlayitRead, PlayitUpdate

DEFAULT_PLAYIT_DOMAIN = "post-stuffed.gl.joinmc.link"
PLAYIT_SETTINGS_ID = 1
PLAYIT_SOCKET_PATH = Path("/host/run/playit/playitd.sock")
PLAYIT_BINARY_PATH = Path("/opt/playit/playit")
PLAYIT_ATTACH_COMMAND = [
    str(PLAYIT_BINARY_PATH),
    "--socket-path",
    str(PLAYIT_SOCKET_PATH),
    "attach",
]
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

router = APIRouter(prefix="/playit", tags=["playit"])
PLAYIT_CONSOLE_QUEUE_MAX = 1000


class PlayitAttachManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self._master_fd: int | None = None
        self._reader: threading.Thread | None = None
        self._output_tail: deque[str] = deque(maxlen=20)
        self._console_history: deque[str] = deque(maxlen=200)
        self._log_subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[str]]] = []
        self._started_at: datetime | None = None
        self._last_status: str = "detached"
        self._last_message: str = "Attach session is not running"
        self._last_published_line: str | None = None

    def status(self) -> tuple[str, str, datetime | None]:
        with self._lock:
            self._refresh_locked()
            return self._last_status, self._last_message, self._started_at

    def start(self) -> tuple[str, str, datetime | None]:
        with self._lock:
            self._refresh_locked()
            if self._process and self._process.poll() is None:
                return self._last_status, self._last_message, self._started_at

            if not PLAYIT_SOCKET_PATH.exists():
                self._last_status = "failed"
                self._last_message = "Playit daemon socket is unavailable"
                self._started_at = None
                self._publish_lines_locked([f"[playit] {self._last_message}"])
                return self._last_status, self._last_message, self._started_at

            if not PLAYIT_BINARY_PATH.exists():
                self._last_status = "failed"
                self._last_message = f"Playit binary not found at {PLAYIT_BINARY_PATH}"
                self._started_at = None
                self._publish_lines_locked([f"[playit] {self._last_message}"])
                return self._last_status, self._last_message, self._started_at

            master_fd: int | None = None
            slave_fd: int | None = None
            try:
                master_fd, slave_fd = pty.openpty()
                process = subprocess.Popen(
                    PLAYIT_ATTACH_COMMAND,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    start_new_session=True,
                    close_fds=True,
                )
                os.close(slave_fd)
                slave_fd = None
            except OSError as exc:
                for fd in (master_fd, slave_fd):
                    if fd is not None:
                        try:
                            os.close(fd)
                        except OSError:
                            pass
                self._last_status = "failed"
                self._last_message = f"Unable to start Playit attach: {exc}"
                self._started_at = None
                self._publish_lines_locked([f"[playit] {self._last_message}"])
                return self._last_status, self._last_message, self._started_at

            self._process = process
            self._master_fd = master_fd
            self._output_tail.clear()
            self._started_at = datetime.now(timezone.utc)
            self._last_status = "attached"
            self._last_message = "Playit attach session is running"
            self._publish_lines_locked([f"[playit] started: {' '.join(PLAYIT_ATTACH_COMMAND)}"])
            self._reader = threading.Thread(target=self._drain_output, args=(master_fd,), daemon=True)
            self._reader.start()
            return self._last_status, self._last_message, self._started_at

    def stop(self) -> tuple[str, str, datetime | None]:
        with self._lock:
            process = self._process
            if process and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    if process.poll() is None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.wait(timeout=5)

            self._close_master_locked()
            self._process = None
            self._started_at = None
            self._last_status = "detached"
            self._last_message = "Playit attach session stopped"
            self._publish_lines_locked([f"[playit] {self._last_message}"])
            return self._last_status, self._last_message, self._started_at

    def subscribe_console(self) -> tuple[asyncio.Queue[str], list[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=PLAYIT_CONSOLE_QUEUE_MAX)
        loop = asyncio.get_running_loop()
        with self._lock:
            self._refresh_locked()
            snapshot = self._snapshot_lines_locked()
            self._log_subscribers.append((loop, queue))
            history = [*self._console_history, *snapshot]
        return queue, history

    def unsubscribe_console(self, queue: asyncio.Queue[str]) -> None:
        with self._lock:
            self._log_subscribers = [
                (loop, subscriber_queue)
                for loop, subscriber_queue in self._log_subscribers
                if subscriber_queue is not queue
            ]

    def _refresh_locked(self) -> None:
        if not self._process:
            return

        return_code = self._process.poll()
        if return_code is None:
            self._last_status = "attached"
            self._last_message = "Playit attach session is running"
            return

        tail = self._latest_output_locked()
        if return_code == 0:
            self._last_status = "detached"
            self._last_message = tail or "Playit attach session exited"
        else:
            self._last_status = "failed"
            self._last_message = tail or f"Playit attach exited with code {return_code}"
        self._publish_lines_locked([f"[playit] {self._last_message}"])
        self._process = None
        self._started_at = None
        self._close_master_locked()

    def _drain_output(self, fd: int) -> None:
        while True:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            text = chunk.decode(errors="replace")
            lines = [self._clean_console_line(line) for line in text.splitlines()]
            lines = [line for line in lines if line]
            with self._lock:
                self._publish_lines_locked(lines)

    def _publish_lines_locked(self, lines: list[str]) -> None:
        filtered_lines: list[str] = []
        for line in lines:
            if line == self._last_published_line:
                continue
            filtered_lines.append(line)
            self._last_published_line = line

        if not filtered_lines:
            return

        lines = filtered_lines
        self._output_tail.extend(lines)
        self._console_history.extend(lines)
        for loop, queue in self._log_subscribers:
            for line in lines:
                loop.call_soon_threadsafe(self._put_line, queue, line)

    @staticmethod
    def _put_line(queue: asyncio.Queue[str], line: str) -> None:
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(line)

    def _latest_output_locked(self) -> str:
        if not self._output_tail:
            return ""
        message = self._output_tail[-1]
        return message[-300:]

    def _snapshot_lines_locked(self) -> list[str]:
        socket_status = "visible" if PLAYIT_SOCKET_PATH.exists() else "unavailable"
        binary_status = "exists" if PLAYIT_BINARY_PATH.exists() else "missing"
        return [
            f"[playit] daemon socket: {socket_status} ({PLAYIT_SOCKET_PATH})",
            f"[playit] binary: {binary_status} ({PLAYIT_BINARY_PATH})",
            f"[playit] attach status: {self._last_status} - {self._last_message}",
            f"[playit] attach command: {' '.join(PLAYIT_ATTACH_COMMAND)}",
        ]

    @staticmethod
    def _clean_console_line(line: str) -> str:
        line = ANSI_ESCAPE_RE.sub("", line)
        line = "".join(char for char in line if char == "\t" or char >= " ")
        return line.strip()

    def _close_master_locked(self) -> None:
        if self._master_fd is None:
            return
        try:
            os.close(self._master_fd)
        except OSError:
            pass
        finally:
            self._master_fd = None


attach_manager = PlayitAttachManager()


async def get_or_create_playit_settings(db: AsyncSession) -> PlayitSettings:
    result = await db.execute(select(PlayitSettings).where(PlayitSettings.id == PLAYIT_SETTINGS_ID))
    settings = result.scalar_one_or_none()
    if settings:
        return settings

    settings = PlayitSettings(id=PLAYIT_SETTINGS_ID, domain=DEFAULT_PLAYIT_DOMAIN)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings


def _read_daemon_status() -> str:
    if PLAYIT_SOCKET_PATH.exists():
        return "running"
    return "unavailable"


def _serialize(settings: PlayitSettings) -> PlayitRead:
    attach_status, attach_message, attach_started_at = attach_manager.status()
    return PlayitRead(
        domain=settings.domain,
        join_address=settings.domain,
        daemon_status=_read_daemon_status(),
        attach_status=attach_status,
        attach_message=attach_message,
        attach_started_at=attach_started_at,
        service_mode="native-systemd",
    )


@router.get("", response_model=PlayitRead)
async def get_playit(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    settings = await get_or_create_playit_settings(db)
    return _serialize(settings)


@router.put("", response_model=PlayitRead)
async def update_playit(
    body: PlayitUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    settings = await get_or_create_playit_settings(db)
    settings.domain = body.domain
    await db.commit()
    await db.refresh(settings)
    return _serialize(settings)


@router.post("/attach", response_model=PlayitRead)
async def attach_playit(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    attach_manager.start()
    settings = await get_or_create_playit_settings(db)
    return _serialize(settings)


@router.delete("/attach", response_model=PlayitRead)
async def detach_playit(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    attach_manager.stop()
    settings = await get_or_create_playit_settings(db)
    return _serialize(settings)

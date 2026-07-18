import asyncio
import json
import logging
import os
import re
import time
from asyncio.subprocess import Process
from enum import Enum
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

CONSOLE_QUEUE_MAX = 2000
DEFAULT_JAVA_BINARY = "java"
RAM_RE = re.compile(r"^(\d+)\s*([KMGT]?B?)$", re.IGNORECASE)


class ServerStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    CRASHED = "crashed"
    STARTING = "starting"
    STOPPING = "stopping"


class ServerController:
    def __init__(self) -> None:
        self._process: Optional[Process] = None
        self._lock = asyncio.Lock()
        self._status = ServerStatus.STOPPED
        self._start_time: Optional[float] = None
        self._active_profile_name: Optional[str] = None
        self._stdout_task: Optional[asyncio.Task] = None
        self._watchdog_task: Optional[asyncio.Task] = None
        # All WebSocket console clients subscribe to this queue
        self._log_subscribers: list[asyncio.Queue] = []
        self._log_file = open(settings.server_log_path, "a", buffering=1, encoding="utf-8")

    def _build_java_command(self, profile) -> list[str]:
        extra_args = json.loads(profile.java_args) if isinstance(profile.java_args, str) else profile.java_args
        cmd = [
            self._java_binary(),
            f"-Xms{self._normalize_ram(profile.ram_min)}",
            f"-Xmx{self._normalize_ram(profile.ram_max)}",
            *extra_args,
            "-jar",
            str(profile.jar_path),
            "--nogui",
        ]
        return cmd

    def _normalize_ram(self, value: str) -> str:
        match = RAM_RE.fullmatch(value.strip())
        if not match:
            raise RuntimeError(f"Invalid RAM value: {value}. Use 1024M, 4G, or 10G.")

        amount, unit = match.groups()
        unit = unit.upper()
        if unit.endswith("B"):
            unit = unit[:-1]
        if not unit:
            unit = "M"
        return f"{amount}{unit}"

    def _java_binary(self) -> str:
        explicit_binary = os.environ.get("JAVA_BINARY")
        if explicit_binary:
            return explicit_binary

        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java_binary = Path(java_home) / "bin" / "java"
            if java_binary.exists():
                return str(java_binary)

        return DEFAULT_JAVA_BINARY

    def eula_path(self, profile) -> Path:
        return settings.worlds_dir / profile.world_name / "eula.txt"

    def eula_accepted(self, profile) -> bool:
        path = self.eula_path(profile)
        if not path.exists():
            return False
        return any(line.strip().lower() == "eula=true" for line in path.read_text(encoding="utf-8", errors="replace").splitlines())

    def accept_eula(self, profile) -> Path:
        path = self.eula_path(profile)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("eula=true\n", encoding="utf-8")
        return path

    async def _java_version_line(self, java_binary: str) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                java_binary,
                "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            output, _ = await process.communicate()
        except Exception as exc:
            return f"unable to read Java version from {java_binary}: {exc}"

        first_line = output.decode("utf-8", errors="replace").splitlines()
        return first_line[0] if first_line else f"{java_binary} -version returned no output"

    async def start(self, profile) -> None:
        async with self._lock:
            if self._status in (ServerStatus.RUNNING, ServerStatus.STARTING):
                raise RuntimeError("Server already running")

            self._status = ServerStatus.STARTING
            self._active_profile_name = profile.name
            cmd = self._build_java_command(profile)
            jar_path = Path(profile.jar_path)
            if not jar_path.exists():
                self._process = None
                self._status = ServerStatus.STOPPED
                self._start_time = None
                self._active_profile_name = None
                raise RuntimeError(f"Server jar not found: {jar_path}")
            if not self.eula_accepted(profile):
                self._process = None
                self._status = ServerStatus.STOPPED
                self._start_time = None
                self._active_profile_name = None
                raise RuntimeError(f"Minecraft EULA not accepted. Click Accept EULA for world '{profile.world_name}' first.")
            await self._broadcast_log(f"[manager] Java runtime: {await self._java_version_line(cmd[0])}\n")
            await self._broadcast_log(f"[manager] Java binary: {cmd[0]}\n")

            try:
                world_dir = settings.worlds_dir / profile.world_name
                world_dir.mkdir(parents=True, exist_ok=True)
                self._process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(world_dir),
                )
            except Exception as e:
                self._process = None
                self._status = ServerStatus.STOPPED
                self._start_time = None
                self._active_profile_name = None
                raise RuntimeError(f"Failed to start server: {e}")

            pid = self._process.pid
            self._start_time = time.time()

            self._status = ServerStatus.RUNNING
            self._stdout_task = asyncio.create_task(self._read_stdout())
            self._watchdog_task = asyncio.create_task(self._watchdog())
            logger.info(f"Server started PID={pid} profile={profile.name}")

    async def stop(self, graceful: bool = True) -> None:
        async with self._lock:
            if self._status not in (ServerStatus.RUNNING, ServerStatus.CRASHED):
                return

            self._status = ServerStatus.STOPPING

            if self._process and graceful:
                try:
                    await self.send_command("stop")
                    try:
                        await asyncio.wait_for(self._process.wait(), timeout=30)
                    except asyncio.TimeoutError:
                        logger.warning("Graceful stop timed out, terminating")
                        self._process.terminate()
                        try:
                            await asyncio.wait_for(self._process.wait(), timeout=5)
                        except asyncio.TimeoutError:
                            self._process.kill()
                except Exception as e:
                    logger.error(f"Error during graceful stop: {e}")
            elif self._process:
                self._process.kill()
                await self._process.wait()

            await self._cleanup()
            logger.info("Server stopped")

    async def _cleanup(self) -> None:
        if self._stdout_task:
            self._stdout_task.cancel()
            self._stdout_task = None
        if self._watchdog_task:
            self._watchdog_task.cancel()
            self._watchdog_task = None
        self._process = None
        self._status = ServerStatus.STOPPED
        self._start_time = None
        self._active_profile_name = None

    async def restart(self, profile) -> None:
        await self.stop()
        await asyncio.sleep(1)
        await self.start(profile)

    async def send_command(self, command: str) -> None:
        command = self._normalize_command(command)
        if self._process and self._process.stdin:
            line = f"{command}\n".encode()
            self._process.stdin.write(line)
            await self._process.stdin.drain()
        else:
            raise RuntimeError("Server not running or stdin unavailable")

    def _normalize_command(self, command: str) -> str:
        command = command.strip()
        if command.startswith("/"):
            command = command[1:].strip()

        lower_command = command.lower()
        time_aliases = {
            "day": "time set day",
            "night": "time set night",
            "noon": "time set noon",
            "midnight": "time set midnight",
        }
        if lower_command in time_aliases:
            return time_aliases[lower_command]

        if lower_command.startswith("set time "):
            return f"time set {command[9:].strip()}"

        return command

    def get_status(self) -> dict:
        uptime = (time.time() - self._start_time) if self._start_time else None
        return {
            "status": self._status.value,
            "pid": self._process.pid if self._process else None,
            "uptime_seconds": uptime,
            "active_profile": self._active_profile_name,
        }

    def subscribe_console(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=CONSOLE_QUEUE_MAX)
        self._log_subscribers.append(q)
        return q

    def unsubscribe_console(self, q: asyncio.Queue) -> None:
        try:
            self._log_subscribers.remove(q)
        except ValueError:
            pass

    async def _broadcast_log(self, line: str) -> None:
        self._log_file.write(line)
        for q in self._log_subscribers:
            try:
                q.put_nowait(line)
            except asyncio.QueueFull:
                pass

    async def _read_stdout(self) -> None:
        if not self._process or not self._process.stdout:
            return
        try:
            async for raw_line in self._process.stdout:
                line = raw_line.decode("utf-8", errors="replace")
                await self._broadcast_log(line)
        except Exception as e:
            logger.error(f"stdout reader error: {e}")

    async def _watchdog(self) -> None:
        if not self._process:
            return
        try:
            await self._process.wait()
            if self._status == ServerStatus.RUNNING:
                logger.warning(f"Server process exited unexpectedly (crashed)")
                await self._cleanup()
                self._status = ServerStatus.CRASHED
        except asyncio.CancelledError:
            pass


server_controller = ServerController()

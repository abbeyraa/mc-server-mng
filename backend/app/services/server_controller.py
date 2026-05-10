import asyncio
import json
import logging
import time
from asyncio.subprocess import Process
from enum import Enum
from typing import Optional

import psutil
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

REDIS_PID_KEY = "mc:server:pid"
REDIS_STATUS_KEY = "mc:server:status"
REDIS_START_TIME_KEY = "mc:server:start_time"
CONSOLE_QUEUE_MAX = 2000


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
        self._redis: Optional[aioredis.Redis] = None
        self._log_file = open(settings.server_log_path, "a", buffering=1, encoding="utf-8")

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def restore_state(self) -> None:
        """On app startup, check Redis for a running PID and restore state."""
        try:
            r = await self._get_redis()
            pid_str = await r.get(REDIS_PID_KEY)
            if pid_str and psutil.pid_exists(int(pid_str)):
                self._status = ServerStatus.RUNNING
                start_time = await r.get(REDIS_START_TIME_KEY)
                self._start_time = float(start_time) if start_time else time.time()
                logger.info(f"Restored running server PID={pid_str}")
            else:
                await r.delete(REDIS_PID_KEY)
                self._status = ServerStatus.STOPPED
        except Exception as e:
            logger.warning(f"State restore failed: {e}")

    def _build_java_command(self, profile) -> list[str]:
        extra_args = json.loads(profile.java_args) if isinstance(profile.java_args, str) else profile.java_args
        cmd = [
            "java",
            f"-Xms{profile.ram_min}",
            f"-Xmx{profile.ram_max}",
            *extra_args,
            "-jar",
            str(profile.jar_path),
            "--nogui",
        ]
        return cmd

    async def start(self, profile) -> None:
        async with self._lock:
            if self._status in (ServerStatus.RUNNING, ServerStatus.STARTING):
                raise RuntimeError("Server already running")

            self._status = ServerStatus.STARTING
            self._active_profile_name = profile.name
            cmd = self._build_java_command(profile)

            try:
                world_dir = settings.worlds_dir / profile.world_name
                self._process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(world_dir),
                )
            except Exception as e:
                self._status = ServerStatus.STOPPED
                raise RuntimeError(f"Failed to start server: {e}")

            pid = self._process.pid
            self._start_time = time.time()

            r = await self._get_redis()
            await r.set(REDIS_PID_KEY, str(pid))
            await r.set(REDIS_START_TIME_KEY, str(self._start_time))

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
        r = await self._get_redis()
        await r.delete(REDIS_PID_KEY)
        await r.delete(REDIS_START_TIME_KEY)

    async def restart(self, profile) -> None:
        await self.stop()
        await asyncio.sleep(1)
        await self.start(profile)

    async def send_command(self, command: str) -> None:
        if self._process and self._process.stdin:
            line = f"{command}\n".encode()
            self._process.stdin.write(line)
            await self._process.stdin.drain()
        else:
            raise RuntimeError("Server not running or stdin unavailable")

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

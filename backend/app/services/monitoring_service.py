import psutil


def _server_process_metrics(pid: int | None) -> dict:
    if not pid or not psutil.pid_exists(pid):
        return {"server_cpu_percent": None, "server_ram_mb": None, "server_pid": None}

    try:
        process = psutil.Process(pid)
        mem = process.memory_info()
        return {
            "server_cpu_percent": process.cpu_percent(interval=None),
            "server_ram_mb": mem.rss // (1024 * 1024),
            "server_pid": pid,
        }
    except (psutil.Error, ProcessLookupError):
        return {"server_cpu_percent": None, "server_ram_mb": None, "server_pid": None}


def get_metrics(server_pid: int | None = None) -> dict:
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_used_mb": mem.used // (1024 * 1024),
        "ram_total_mb": mem.total // (1024 * 1024),
        "ram_percent": mem.percent,
        "disk_used_gb": disk.used // (1024 ** 3),
        "disk_total_gb": disk.total // (1024 ** 3),
        "disk_percent": disk.percent,
        **_server_process_metrics(server_pid),
    }

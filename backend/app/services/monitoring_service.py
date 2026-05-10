import psutil


def get_metrics() -> dict:
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
    }

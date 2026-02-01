"""Core metrics collection for Valkey/Redis servers and Linux system memory."""

import dataclasses
import datetime as dt
import time
from typing import Iterator, Optional

import redis


@dataclasses.dataclass(frozen=True, slots=True)
class MetricSnapshot:
    """Immutable record of a single sampling instant."""

    timestamp: str  # "YYYY-MM-DD HH:MM:SS"
    epoch: float  # time.time()

    # Valkey stats
    ops_per_sec: int
    cpu_user_per_sec: float  # nan on first sample
    cpu_sys_per_sec: float  # nan on first sample
    used_mib: float
    rss_mib: float
    peak_mib: float
    frag_ratio: float

    # Linux system memory (/proc/meminfo)
    cache_mib: float
    buffers_mib: float
    kernel_mib: float

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


class MetricsCollector:
    """Connects to a Valkey/Redis server and produces MetricSnapshot objects.

    Tracks CPU counters internally so callers receive ready-to-display
    per-second rates without managing any state.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self._client = redis.Redis(
            host=host,
            port=port,
            username=username,
            password=password,
            decode_responses=True,
        )
        self._client.ping()
        self._prev_user: Optional[float] = None
        self._prev_sys: Optional[float] = None
        self._prev_ts: Optional[float] = None

    def collect_once(self) -> MetricSnapshot:
        """Take a single sample.  Updates internal state for CPU rates."""
        now = time.time()
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mem = self._client.info("memory")
        cpu = self._client.info("cpu")
        stats = self._client.info("stats")

        user = cpu.get("used_cpu_user")
        sysc = cpu.get("used_cpu_sys")

        cpu_u = cpu_s = float("nan")
        if self._prev_ts is not None:
            dt_s = now - self._prev_ts
            if dt_s > 0:
                cpu_u = (user - self._prev_user) / dt_s
                cpu_s = (sysc - self._prev_sys) / dt_s

        self._prev_user, self._prev_sys, self._prev_ts = user, sysc, now

        cache_mib, buf_mib, kern_mib = self._read_system_memory()

        return MetricSnapshot(
            timestamp=ts,
            epoch=now,
            ops_per_sec=stats.get("instantaneous_ops_per_sec", 0),
            cpu_user_per_sec=cpu_u,
            cpu_sys_per_sec=cpu_s,
            used_mib=self._mib(mem.get("used_memory")),
            rss_mib=self._mib(mem.get("used_memory_rss")),
            peak_mib=self._mib(mem.get("used_memory_peak")),
            frag_ratio=mem.get("mem_fragmentation_ratio", float("nan")),
            cache_mib=cache_mib,
            buffers_mib=buf_mib,
            kernel_mib=kern_mib,
        )

    def stream(self, interval: float) -> Iterator[MetricSnapshot]:
        """Infinite generator yielding a snapshot every *interval* seconds."""
        while True:
            yield self.collect_once()
            time.sleep(interval)

    @staticmethod
    def _mib(b) -> float:
        return b / (1024 * 1024) if b is not None else float("nan")

    @staticmethod
    def _read_system_memory() -> tuple[float, float, float]:
        info: dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v, *_ = line.split()
                info[k.rstrip(":")] = int(v)
        cache = info["Cached"] + info.get("SReclaimable", 0) - info.get("Shmem", 0)
        kernel = (
            info.get("Slab", 0)
            + info.get("KernelStack", 0)
            + info.get("PageTables", 0)
            + info.get("VmallocUsed", 0)
        )
        return cache / 1024, info.get("Buffers", 0) / 1024, kernel / 1024

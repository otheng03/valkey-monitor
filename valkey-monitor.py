#!/usr/bin/env python3
"""
valkey_stat.py
- Print Valkey CPU & memory stats + system buffer/cache/kernel
- Tabular output
- Header is re-printed every N rows
"""

import argparse
import datetime as dt
import time
import sys

try:
    import redis
except ImportError:
    print("Missing dependency: redis (pip install redis)", file=sys.stderr)
    raise


# -------------------------
# CLI
# -------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=6379)
    p.add_argument("--password")
    p.add_argument("--username")
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--header-every", type=int, default=20)
    return p.parse_args()


# -------------------------
# Helpers
# -------------------------
def mib(b):
    return b / (1024 * 1024) if b is not None else float("nan")


def read_meminfo():
    out = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, v, *_ = line.split()
            out[k.rstrip(":")] = int(v)
    return out


def system_memory():
    m = read_meminfo()
    cache = m["Cached"] + m.get("SReclaimable", 0) - m.get("Shmem", 0)
    kernel = (
        m.get("Slab", 0)
        + m.get("KernelStack", 0)
        + m.get("PageTables", 0)
        + m.get("VmallocUsed", 0)
    )
    return (
        cache / 1024,
        m.get("Buffers", 0) / 1024,
        kernel / 1024,
    )


# -------------------------
# Main
# -------------------------
def main():
    args = parse_args()

    r = redis.Redis(
            host=args.host,
            port=args.port,
            password=args.password,
            username=args.username,
            decode_responses=True,
            )

    r.ping()

    prev_user = prev_sys = None
    prev_ts = None
    line_no = 0

    header = (
        f"{'TIME':19} "
        f"{'OPS/s':>7} "
        f"{'CPU_U/s':>8} {'CPU_S/s':>8} "
        f"{'USED(MiB)':>9} {'RSS(MiB)':>9} {'PEAK(MiB)':>10} {'FRAG':>6} "
        f"{'CACHE(MiB)':>11} {'BUF(MiB)':>9} {'KERNEL(MiB)':>12}"
    )

    while True:
        now = time.time()
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mem = r.info("memory")
        cpu = r.info("cpu")
        stats = r.info("stats")

        used = mib(mem.get("used_memory"))
        rss = mib(mem.get("used_memory_rss"))
        peak = mib(mem.get("used_memory_peak"))
        frag = mem.get("mem_fragmentation_ratio", float("nan"))

        ops = stats.get("instantaneous_ops_per_sec", 0)

        user = cpu.get("used_cpu_user")
        sysc = cpu.get("used_cpu_sys")

        cpu_u = cpu_s = float("nan")
        if prev_ts is not None:
            dt_s = now - prev_ts
            cpu_u = (user - prev_user) / dt_s
            cpu_s = (sysc - prev_sys) / dt_s

        cache, buffers, kernel = system_memory()

        if line_no % args.header_every == 0:
            print(header)

        print(
            f"{ts} "
            f"{ops:7d} "
            f"{cpu_u:8.3f} {cpu_s:8.3f} "
            f"{used:9.1f} {rss:9.1f} {peak:10.1f} {frag:6.2f} "
            f"{cache:11.1f} {buffers:9.1f} {kernel:12.1f}",
            flush=True,
        )

        prev_user, prev_sys, prev_ts = user, sysc, now
        line_no += 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()


"""Terminal frontend -- preserves the original valkey-monitor tabular output."""

from .cli import make_terminal_parser
from .collector import MetricsCollector

HEADER = (
    f"{'TIME':19} "
    f"{'OPS/s':>7} "
    f"{'CPU_U/s':>8} {'CPU_S/s':>8} "
    f"{'USED(MiB)':>9} {'RSS(MiB)':>9} {'PEAK(MiB)':>10} {'FRAG':>6} "
    f"{'CACHE(MiB)':>11} {'BUF(MiB)':>9} {'KERNEL(MiB)':>12}"
)


def format_row(s) -> str:
    """Format a MetricSnapshot as a fixed-width terminal row."""
    return (
        f"{s.timestamp} "
        f"{s.ops_per_sec:7d} "
        f"{s.cpu_user_per_sec:8.3f} {s.cpu_sys_per_sec:8.3f} "
        f"{s.used_mib:9.1f} {s.rss_mib:9.1f} {s.peak_mib:10.1f} {s.frag_ratio:6.2f} "
        f"{s.cache_mib:11.1f} {s.buffers_mib:9.1f} {s.kernel_mib:12.1f}"
    )


def main():
    args = make_terminal_parser().parse_args()
    collector = MetricsCollector(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
    )
    for i, snapshot in enumerate(collector.stream(args.interval)):
        if i % args.header_every == 0:
            print(HEADER)
        print(format_row(snapshot), flush=True)


if __name__ == "__main__":
    main()

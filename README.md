# valkey-monitor

A Valkey/Redis metrics monitor with two frontends:

- **Terminal** -- tabular output to stdout (the original behaviour)
- **Web** -- real-time charts in the browser via Server-Sent Events

## Output columns

| Column | Description |
|---|---|
| `TIME` | Timestamp of the sample |
| `OPS/s` | Instantaneous operations per second |
| `CPU_U/s` | User CPU seconds consumed per second |
| `CPU_S/s` | System CPU seconds consumed per second |
| `USED(MiB)` | Valkey `used_memory` |
| `RSS(MiB)` | Valkey resident set size |
| `PEAK(MiB)` | Valkey peak memory usage |
| `FRAG` | Memory fragmentation ratio |
| `CACHE(MiB)` | Linux page cache (from `/proc/meminfo`) |
| `BUF(MiB)` | Linux buffer memory |
| `KERNEL(MiB)` | Linux kernel memory (slab + kernel stack + page tables + vmalloc) |

## Requirements

- Python 3.10+
- Linux (reads `/proc/meminfo`)
- A running Valkey or Redis-compatible server

## Install

Terminal frontend only:

```
pip install .
```

With the web dashboard:

```
pip install '.[web]'
```

## Usage

### Terminal

```
valkey-monitor [OPTIONS]
```

or directly:

```
python valkey-monitor.py [OPTIONS]
```

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Server hostname or IP |
| `--port` | `6379` | Server port |
| `--username` | None | Username for ACL auth |
| `--password` | None | Password |
| `--interval` | `1.0` | Seconds between samples |
| `--header-every` | `20` | Re-print the header every N rows |

#### Example

```
$ valkey-monitor --host 10.0.0.5 --interval 2
TIME                  OPS/s  CPU_U/s  CPU_S/s USED(MiB)  RSS(MiB)  PEAK(MiB)   FRAG  CACHE(MiB) BUF(MiB)  KERNEL(MiB)
2025-06-15 12:00:00       0      nan      nan      52.3      58.1       58.1   1.11      1024.3     128.5        312.7
2025-06-15 12:00:02     142    0.032    0.015      52.3      58.1       58.1   1.11      1024.3     128.5        312.8
```

The first row always shows `nan` for CPU columns because per-second rates require two samples.

### Web dashboard

```
valkey-monitor-web [OPTIONS]
```

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Valkey server hostname or IP |
| `--port` | `6379` | Valkey server port |
| `--username` | None | Username for ACL auth |
| `--password` | None | Password |
| `--interval` | `1.0` | Seconds between samples |
| `--bind` | `0.0.0.0` | Web server bind address |
| `--web-port` | `8080` | Web server port |
| `--history` | `300` | Max data points kept in memory |

Open `http://localhost:8080` in a browser to see live-updating charts for all metrics.

## Project structure

```
valkey_monitor/
  __init__.py
  collector.py     # shared: MetricsCollector + MetricSnapshot
  cli.py           # shared: argument parsing
  terminal.py      # terminal frontend
  server.py        # web frontend entry point
  web/
    app.py         # Flask app with SSE
    templates/     # HTML
    static/        # JS + CSS
```

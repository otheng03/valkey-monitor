# valkey-monitor

A command-line tool that continuously prints Valkey CPU and memory statistics alongside Linux system memory (buffer/cache/kernel) in a tabular format.

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

- Python 3
- Linux (reads `/proc/meminfo`)
- A running Valkey or Redis-compatible server

## Install

```
pip install -r requirements.txt
```

## Usage

```
python valkey-monitor.py [OPTIONS]
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Server hostname or IP |
| `--port` | `6379` | Server port |
| `--username` | | Username for ACL auth |
| `--password` | | Password |
| `--interval` | `1.0` | Seconds between samples |
| `--header-every` | `20` | Re-print the header every N rows |

### Example

```
$ python valkey-monitor.py --host 10.0.0.5 --interval 2
TIME                  OPS/s  CPU_U/s  CPU_S/s USED(MiB)  RSS(MiB)  PEAK(MiB)   FRAG  CACHE(MiB) BUF(MiB)  KERNEL(MiB)
2025-06-15 12:00:00       0      nan      nan      52.3      58.1       58.1   1.11      1024.3     128.5        312.7
2025-06-15 12:00:02     142    0.032    0.015      52.3      58.1       58.1   1.11      1024.3     128.5        312.8
```

The first row always shows `nan` for CPU columns because per-second rates require two samples.

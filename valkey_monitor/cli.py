"""Shared and per-frontend CLI argument parsing."""

import argparse


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add connection and sampling arguments shared by all frontends."""
    parser.add_argument("--host", default="127.0.0.1",
                        help="Valkey/Redis server hostname (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6379,
                        help="Server port (default: 6379)")
    parser.add_argument("--username", default=None,
                        help="Username for ACL auth")
    parser.add_argument("--password", default=None,
                        help="Password")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Seconds between samples (default: 1.0)")


def make_terminal_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Valkey monitor -- terminal frontend")
    add_common_args(p)
    p.add_argument("--header-every", type=int, default=20,
                   help="Re-print header every N rows (default: 20)")
    return p


def make_web_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Valkey monitor -- web dashboard")
    add_common_args(p)
    p.add_argument("--bind", default="0.0.0.0",
                   help="Web server bind address (default: 0.0.0.0)")
    p.add_argument("--web-port", type=int, default=8080,
                   help="Web server port (default: 8080)")
    p.add_argument("--history", type=int, default=300,
                   help="Max data points kept in memory (default: 300)")
    return p

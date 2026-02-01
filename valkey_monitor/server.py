"""Web dashboard entry point."""

from .cli import make_web_parser
from .collector import MetricsCollector
from .web.app import create_app


def main():
    args = make_web_parser().parse_args()
    collector = MetricsCollector(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
    )
    app = create_app(collector, interval=args.interval, max_history=args.history)
    app.run(host=args.bind, port=args.web_port, threaded=True)


if __name__ == "__main__":
    main()

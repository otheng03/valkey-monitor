"""Flask application with SSE streaming for real-time metrics."""

import json
import math
import threading
import time
from collections import deque

from flask import Flask, Response, jsonify, render_template

from ..collector import MetricsCollector


def _sanitize_for_json(d: dict) -> dict:
    """Replace NaN/Inf with None for JSON compliance."""
    return {
        k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
        for k, v in d.items()
    }


def create_app(
    collector: MetricsCollector,
    interval: float,
    max_history: int = 300,
) -> Flask:
    """Application factory.  Returns a configured Flask app."""

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    history: deque = deque(maxlen=max_history)
    lock = threading.Lock()
    new_data = threading.Condition(lock)

    def _collector_loop():
        while True:
            snapshot = collector.collect_once()
            with new_data:
                history.append(snapshot)
                new_data.notify_all()
            time.sleep(interval)

    t = threading.Thread(target=_collector_loop, daemon=True)
    t.start()

    @app.route("/")
    def index():
        return render_template("index.html", interval=interval)

    @app.route("/api/history")
    def api_history():
        with lock:
            data = [_sanitize_for_json(s.as_dict()) for s in history]
        return jsonify(data)

    @app.route("/api/stream")
    def api_stream():
        def generate():
            last_epoch = 0.0
            while True:
                with new_data:
                    new_data.wait(timeout=interval * 2)
                    pending = [s for s in history if s.epoch > last_epoch]
                if pending:
                    for s in pending:
                        payload = json.dumps(_sanitize_for_json(s.as_dict()))
                        yield f"data: {payload}\n\n"
                        last_epoch = s.epoch

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return app

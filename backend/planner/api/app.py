"""Flask application factory."""

from __future__ import annotations

from typing import Any
from flask import Flask, jsonify


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)

    if test_config is not None:
        app.config.update(test_config)

    @app.route("/health", methods=["GET"])
    def health_check():
        """Service health check endpoint."""
        return jsonify({
            "status": "ok",
            "version": "0.1.0"
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)

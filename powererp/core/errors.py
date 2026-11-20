"""One error type for the whole ERP and one handler that turns it into the API's JSON error.

Body: {"error": code, "field": field (optional), "detail": detail (optional)} with the HTTP status of the error.
"""

from __future__ import annotations

from flask import Flask, jsonify


class AppError(Exception):
    """A business or validation error shown to the user: `code` is translated by the screens (err.<code>)."""

    status = 400

    def __init__(self, code: str, field: str | None = None, status: int | None = None, detail: str | None = None):
        super().__init__(code)
        self.code = code
        self.field = field
        self.detail = detail
        if status is not None:
            self.status = status

    def to_dict(self) -> dict:
        body = {"error": self.code}
        if self.field:
            body["field"] = self.field
        if self.detail:
            body["detail"] = self.detail
        return body


class NotFound(AppError):
    status = 404

    def __init__(self, code: str = "not_found", **kw):
        super().__init__(code, **kw)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _app_error(err: AppError):
        return jsonify(err.to_dict()), err.status

    @app.errorhandler(404)
    def _not_found(_err):
        return jsonify({"error": "not_found"}), 404

"""Administration > Audit log: the audit trail of the ERP (see service.py).

GET /api/audit?from=&to=&user=&kind=&event=&screen=&q=&page=&size=   the events, newest first (administrator)
GET /api/audit/export?... (+ lang)                                    the same as a spreadsheet (.xlsx)
GET /api/audit/filters                                                the user names and events found in the log
Every call that changes data is kept by an after_request hook (registered before the commit of the request, so it
runs after it: a change is kept only once it is saved).
"""

from __future__ import annotations

from flask import Blueprint, Flask, Response, jsonify, request

from powererp.container import Container
from powererp.core.security import current_username
from powererp.core.values import text

from .service import AuditService, record_of, screen_action

__all__ = ["AuditService", "client_ip", "register"]

WRITES = ("POST", "PUT", "PATCH", "DELETE")


def client_ip() -> str:
    """The caller's address: the first X-Forwarded-For hop when a proxy sends one (Docker / nginx), else the peer."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() if forwarded else "") or text(request.remote_addr)


def _hook(audit: AuditService):
    def keep(response):
        path = request.path
        if not path.startswith("/api/") and not path.startswith("/cgi-bin/"):
            return response
        args = dict(request.view_args or {})
        if response.status_code == 403 and request.endpoint != "auth.login":
            audit.record(
                "security",
                "access_denied",
                current_username(),
                method=request.method,
                path=path,
                status=403,
                ip=client_ip(),
            )
            return response
        if request.method not in WRITES or response.status_code >= 400:
            return response
        what = screen_action(request.endpoint, request.method, args)
        if what is None:
            return response
        answer = response.get_json(silent=True) if response.is_json else None
        audit.record(
            "change",
            what[1],
            current_username(),
            screen=what[0],
            method=request.method,
            path=path,
            record=record_of(args, answer),
            status=response.status_code,
            ip=client_ip(),
            details={"sent": request.get_json(silent=True)} if request.is_json else {},
        )
        return response

    return keep


def register(app: Flask, c: Container) -> AuditService:
    audit = c.register("audit", AuditService())
    app.after_request(_hook(audit))
    bp = Blueprint("audit", __name__)

    @bp.route("/api/audit")
    def audit_list():
        return jsonify(audit.page(request.args))

    @bp.route("/api/audit/filters")
    def audit_filters():
        return jsonify(audit.filters())

    @bp.route("/api/audit/export")
    def audit_export():
        data = audit.export(request.args, text(request.args.get("lang")) or "en")
        return Response(
            data,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="audit-log.xlsx"'},
        )

    app.register_blueprint(bp)
    return audit

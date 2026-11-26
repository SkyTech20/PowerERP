"""Administration > Personal data (Quebec Law 25, item 9 of the SCOR / ISO plan; administrator only, see service.py).

GET  /api/privacy/policy                      the person in charge, where the data is hosted, the retention rule
PUT  /api/privacy/policy                      save them
GET  /api/privacy/search?q=                   the persons whose name, user name, e-mail or phone contains q
GET  /api/privacy/<kind>/<ref>                a person's file: what is kept, the documents, the audit events
GET  /api/privacy/<kind>/<ref>/export?format=json|xlsx&lang=   the file to give the person
POST /api/privacy/<kind>/<ref>/anonymize      anonymize the person (cannot be undone)
GET  /api/privacy/retention                   the persons kept longer than the retention rule
POST /api/privacy/retention/apply             anonymize them
"""

from __future__ import annotations

from flask import Blueprint, Flask, Response, jsonify, request

from powererp import settings
from powererp.container import Container
from powererp.core.errors import NotFound
from powererp.core.security import current_username
from powererp.core.values import text
from powererp.modules.audit import client_ip

from .service import PrivacyService

__all__ = ["PrivacyService", "register"]


def register(app: Flask, c: Container) -> PrivacyService:
    privacy = c.register("privacy", PrivacyService(settings.get_setting, settings.set_setting))
    bp = Blueprint("privacy", __name__)

    @bp.route("/api/privacy/policy", methods=["GET", "PUT"])
    def privacy_policy():
        if request.method == "PUT":
            return jsonify(privacy.save_policy(request.get_json(silent=True)))
        return jsonify(privacy.policy())

    @bp.route("/api/privacy/search")
    def privacy_search():
        return jsonify({"items": privacy.search(text(request.args.get("q")))})

    @bp.route("/api/privacy/retention")
    def privacy_retention():
        return jsonify(privacy.due())

    @bp.route("/api/privacy/retention/<action>", methods=["POST"])
    def privacy_retention_apply(action):
        if action != "apply":
            raise NotFound()
        return jsonify(privacy.apply_retention(current_username()))

    @bp.route("/api/privacy/<kind>/<ref>/export")
    def privacy_export(kind, ref):
        body, mimetype, name = privacy.export(
            kind, ref, text(request.args.get("format")) or "json", text(request.args.get("lang")) or "en"
        )
        return Response(body, mimetype=mimetype, headers={"Content-Disposition": f'attachment; filename="{name}"'})

    @bp.route("/api/privacy/<kind>/<ref>/<action>", methods=["POST"])
    def privacy_action(kind, ref, action):
        if action != "anonymize":
            raise NotFound()
        done = privacy.anonymize(kind, ref, current_username())
        ref = done["name"] if kind == "former" else ref  # the path named the person: kept with the new name
        c.get("audit").record(
            "change",
            "anonymize",
            current_username(),
            screen="admin.privacy",
            method="POST",
            path=f"/api/privacy/{kind}/{ref}/anonymize",
            record=f"{kind}/{ref}",
            status=200,
            ip=client_ip(),
            details={"changed": done["changed"]},
        )
        return jsonify(done)

    @bp.route("/api/privacy/<kind>/<ref>")
    def privacy_file(kind, ref):
        return jsonify(privacy.file(kind, ref))

    app.register_blueprint(bp)
    return privacy

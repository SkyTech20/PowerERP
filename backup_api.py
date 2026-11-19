"""
PowerERP — Administration > Backups (administrators only, see auth.py).

  GET    /api/admin/backup                 settings, last result, next run and the backup files
  PUT    /api/admin/backup                 save the settings {enabled, intervalHours, path, keep}
  POST   /api/admin/backup/run             make a backup now
  GET    /api/admin/backup/files/<name>    download a backup file

The work is in powererp/backup.py (pg_dump, rotation, scheduler).
"""
from flask import Blueprint, jsonify, request, send_file

from powererp import backup

bp = Blueprint("backup", __name__)


@bp.errorhandler(backup.BackupError)
def _error(e):
    body = {"error": e.code}
    if e.field:
        body["field"] = e.field
    if e.detail:
        body["detail"] = e.detail
    status = 409 if e.code == "backup_running" else 500 if e.code in ("backup_failed", "pg_dump_missing") else 400
    return jsonify(body), status


def _state():
    settings = backup.get_settings()
    status = backup.get_status()
    return {"settings": settings, "status": status, "nextRun": backup.next_run(settings, status),
            "files": backup.list_files(settings)}


@bp.route("/api/admin/backup", methods=["GET", "PUT"])
def backup_settings():
    if request.method == "PUT":
        p = request.get_json(silent=True)
        if not isinstance(p, dict):
            return jsonify({"error": "invalid_body"}), 400
        backup.save_settings(p)
    return jsonify(_state())


@bp.route("/api/admin/backup/run", methods=["POST"])
def backup_run():
    backup.run_backup("manual")
    return jsonify(_state())


@bp.route("/api/admin/backup/files/<name>")
def backup_file(name):
    path = backup.file_path(name)
    if path is None:
        return jsonify({"error": "not_found"}), 404
    return send_file(path.resolve(), as_attachment=True, download_name=name, mimetype="application/octet-stream")


def register_backup(app):
    app.register_blueprint(bp)
    if not app.config.get("TESTING"):
        backup.start_scheduler()

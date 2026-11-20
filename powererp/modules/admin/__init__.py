"""
Administration module: Backups (administrators only, see powererp.modules.auth).

  GET    /api/admin/backup                 settings, last result, next run and the backup files
  PUT    /api/admin/backup                 save the settings {enabled, intervalHours, path, keep}
  POST   /api/admin/backup/run             make a backup now
  GET    /api/admin/backup/files/<name>    download a backup file

The work is in backup.py (pg_dump, rotation, scheduler).
"""

from flask import Blueprint, jsonify, request, send_file

from . import backup

bp = Blueprint("backup", __name__)


def _state():
    settings = backup.get_settings()
    status = backup.get_status()
    return {
        "settings": settings,
        "status": status,
        "nextRun": backup.next_run(settings, status),
        "files": backup.list_files(settings),
    }


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


def register(app):
    app.register_blueprint(bp)
    if not app.config.get("TESTING"):
        backup.start_scheduler()

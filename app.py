"""
PowerERP: entry point (python app.py, or a WSGI server with app:app).

The application is built by powererp.factory.create_app(): database (DATABASE_URL, PostgreSQL), login,
the ERP modules, the PowerWARE web services used by SkyAI, backups, and the demo data of an empty database.

Run:  docker compose up -d db && pip install -r requirements.txt && python app.py
Open: http://localhost:5050/
"""

import os

from powererp.container import container_of
from powererp.factory import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    c = container_of(app)
    print(f"PowerERP: http://localhost:{port}/ (data: {c.get('demo').name}, database: {c.get('database_url')})")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py erp_api.py powerware_api.py purchasing_api.py inventory_api.py db.py auth.py alembic.ini ./
COPY powererp/ ./powererp/
COPY migrations/ ./migrations/
COPY static/ ./static/
COPY data/ ./data/

# Database: PostgreSQL, set DATABASE_URL (postgresql://user:password@host:5432/powererp).
# The schema is created and migrated by the ERP when it starts (Alembic).
ENV PORT=5050
EXPOSE 5050

CMD ["python", "app.py"]

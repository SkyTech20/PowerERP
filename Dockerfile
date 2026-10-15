FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py erp_api.py powerware_api.py db.py auth.py ./
COPY static/ ./static/
COPY data/ ./data/

# SQLite database (users + ERP data). Mount /app/db as a volume to keep it.
RUN mkdir -p /app/db
VOLUME /app/db

ENV ERP_DB_PATH=/app/db/powererp.db \
    PORT=5050
EXPOSE 5050

CMD ["python", "app.py"]

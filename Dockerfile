FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py erp_api.py powerware_api.py ./
COPY static/ ./static/
COPY data/ ./data/

ENV PORT=5050
EXPOSE 5050

CMD ["python", "app.py"]

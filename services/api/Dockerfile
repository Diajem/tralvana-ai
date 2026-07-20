FROM python:3.12-slim

WORKDIR /app

COPY services/api/requirements.txt services/api/requirements.txt
RUN pip install --no-cache-dir -r services/api/requirements.txt

COPY services services
COPY ai ai
COPY travelos travelos

ENV PYTHONPATH=/app:/app/services/api

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --app-dir services/api --host 0.0.0.0 --port ${PORT:-8000}"]

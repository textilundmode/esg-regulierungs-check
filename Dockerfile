FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py llm.py views.py fetcher.py regulations.py i18n.py ./
COPY templates/ templates/

RUN mkdir -p /app/data && chmod 777 /app/data

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "--timeout", "300", "app:app"]

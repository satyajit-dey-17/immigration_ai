FROM python:3.11-slim-bullseye

RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl wget gnupg \
    && rm -rf /var/lib/apt/lists/*
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prom_multiproc
RUN mkdir -p /tmp/prom_multiproc
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

EXPOSE 8000

CMD ["python", "scheduler.py"]
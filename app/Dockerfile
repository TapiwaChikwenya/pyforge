# PyForge learning app (local mode)
# python:3.11-slim + a headless JRE so in-app PySpark exercises run.
FROM python:3.11-slim

# Java for PySpark local mode (exercises fs-3, ss-3)
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 pyforge

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Progress + rate-limit DB live here; writable by the non-root user.
RUN mkdir -p /app/data && chown -R pyforge:pyforge /app/data

USER pyforge

ENV PYTHONUNBUFFERED=1 \
    PYFORGE_MODE=local

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz').read()"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

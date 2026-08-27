FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

RUN groupadd --system app && useradd --system --gid app --create-home app
WORKDIR /app

COPY requirements-core.txt requirements-ocr.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements-core.txt && \
    pip install -r requirements-ocr.txt

RUN apt-get update && \
    apt-get install --yes --no-install-recommends libgomp1 libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY docker-entrypoint.sh /usr/local/bin/veda-entrypoint
RUN chown -R app:app /app && chmod 755 /usr/local/bin/veda-entrypoint

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
ENTRYPOINT ["/usr/local/bin/veda-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

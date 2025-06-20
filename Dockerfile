# ───────────────────────────────────────── base image
FROM python:3.12-slim

# — выводим логи напрямую, а не буфер
ENV PYTHONUNBUFFERED=1

# ───────────────────────────────────────── system deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# ───────────────────────────────────────── workdir
WORKDIR /app

# ───────────────────────────────────────── python deps
#
# 1. requirements.txt кладём отдельно – так кеш не
#    инвалиируется при каждом изменении исходников.
# 2. если в проекте уже есть poetry/pyproject – замените
#    этот блок на установку через Poetry/PDM.
#
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ───────────────────────────────────────── source code
COPY . .

# ───────────────────────────────────────── start command
RUN chmod +x /app/migrate.sh
ENTRYPOINT ["/app/migrate.sh"]
CMD ["python", "main.py"]

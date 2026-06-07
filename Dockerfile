FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Collect static at build time so the image is self-contained.
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Render/Cloudflare set $PORT; default to 8000 locally.
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]

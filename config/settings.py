"""
Django settings for Options Lab.

Deliberately lean: no database is required for the quant math (modules under
`lab/` are framework-free and cache to disk). SQLite stays configured only so
Django's own machinery runs; add models later only if persisting backtest runs.

Configuration is read from the environment so the same image runs locally and
on Render behind Cloudflare. See `.env.example`.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key-change-in-production")

DEBUG = env_bool("DJANGO_DEBUG", default=True)

# Comma-separated hosts; "*" by default for the demo. Tighten on deploy.
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Cloudflare/Render terminate TLS in front of us; trust the forwarded origin.
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "lab",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Minimal DB so Django runs; the quant core does not use it.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

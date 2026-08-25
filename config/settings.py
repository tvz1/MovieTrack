"""
Django settings for config project.
"""

from pathlib import Path
from datetime import timedelta
import os

import dj_database_url
from dotenv import load_dotenv


# =========================================================
# PATHS + ENVIRONMENT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env"
)


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = (
    os.getenv("DJANGO_SECRET_KEY")
    or os.getenv("SECRET_KEY")
)

if not SECRET_KEY:
    raise RuntimeError(
        "Django SECRET_KEY is missing."
    )


IS_RENDER = (
    os.getenv("RENDER") == "true"
)


DEBUG = (
    os.getenv(
        "DJANGO_DEBUG",
        "False",
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)

# Render mora raditi s DEBUG=False.
if IS_RENDER:
    DEBUG = False


allowed_hosts_env = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,10.0.2.2",
)

ALLOWED_HOSTS = [
    host.strip()
    for host in allowed_hosts_env.split(",")
    if host.strip()
]


render_hostname = os.getenv(
    "RENDER_EXTERNAL_HOSTNAME"
)

if render_hostname:
    ALLOWED_HOSTS.append(
        render_hostname
    )


# =========================================================
# TMDB
# =========================================================

TMDB_ACCESS_TOKEN = os.getenv(
    "TMDB_ACCESS_TOKEN"
)

if not TMDB_ACCESS_TOKEN:
    raise RuntimeError(
        "TMDB_ACCESS_TOKEN is missing."
    )


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",

    "movies",
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URLS / WSGI
# =========================================================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# =========================================================
# DATABASE
# =========================================================

database_url = os.getenv(
    "DATABASE_URL"
)


if database_url:
    DATABASES = {
        "default":
            dj_database_url.config(
                default=database_url,
                conn_max_age=600,
                conn_health_checks=True,
            )
    }

else:
    DB_ENGINE = os.getenv(
        "DB_ENGINE",
        "sqlite",
    ).lower()

    if DB_ENGINE == "postgres":
        DATABASES = {
            "default": {
                "ENGINE":
                    "django.db.backends.postgresql",

                "NAME":
                    os.getenv(
                        "POSTGRES_DB",
                        "movietrack",
                    ),

                "USER":
                    os.getenv(
                        "POSTGRES_USER",
                        "movietrack",
                    ),

                "PASSWORD":
                    os.getenv(
                        "POSTGRES_PASSWORD",
                        "",
                    ),

                "HOST":
                    os.getenv(
                        "POSTGRES_HOST",
                        "127.0.0.1",
                    ),

                "PORT":
                    os.getenv(
                        "POSTGRES_PORT",
                        "5432",
                    ),
            }
        }

    else:
        DATABASES = {
            "default": {
                "ENGINE":
                    "django.db.backends.sqlite3",

                "NAME":
                    BASE_DIR / "db.sqlite3",
            }
        }


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME":
            "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME":
            "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME":
            "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = "/static/"

STATIC_ROOT = (
    BASE_DIR / "staticfiles"
)

STORAGES = {
    "default": {
        "BACKEND":
            "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND":
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# =========================================================
# EMAIL
# =========================================================

# Ako SMTP varijable nisu postavljene, lokalno ispisuj mail
# u terminal. Na Renderu postavi SMTP varijable i Django će
# automatski koristiti pravi SMTP server.
EMAIL_HOST = os.getenv(
    "EMAIL_HOST",
    "",
)

EMAIL_PORT = int(
    os.getenv(
        "EMAIL_PORT",
        "587",
    )
)

EMAIL_HOST_USER = os.getenv(
    "EMAIL_HOST_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    "",
)

EMAIL_USE_TLS = (
    os.getenv(
        "EMAIL_USE_TLS",
        "True",
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)

EMAIL_USE_SSL = (
    os.getenv(
        "EMAIL_USE_SSL",
        "False",
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER
    or "WatchLibrary <noreply@watchlibrary.local>",
)

if EMAIL_HOST:
    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend"
    )
else:
    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
    )


# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}


# =========================================================
# SIMPLE JWT
# =========================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":
        timedelta(
            minutes=15,
        ),

    "REFRESH_TOKEN_LIFETIME":
        timedelta(
            days=30,
        ),
}


# =========================================================
# SECURITY - PRODUCTION
# =========================================================

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)
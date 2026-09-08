from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


load_dotenv(BASE_DIR / ".env")


# ============================================================
# CORE SETTINGS
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-development-key-change-me",
)

DEBUG = os.getenv(
    "DEBUG",
    "True",
).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]


# ============================================================
# SECURITY
# ============================================================

SECURE_SSL_REDIRECT = (
    os.getenv(
        "SECURE_SSL_REDIRECT",
        "False",
    ).lower() == "true"
)


# ============================================================
# SESSION / COOKIE SECURITY
# ============================================================

# Use a ProblemPool-specific session cookie name.
# This prevents collisions with other Django projects running
# on the same local hostname.
SESSION_COOKIE_NAME = "problempool_sessionid"

# Keep the cookie available to the entire ProblemPool site.
SESSION_COOKIE_PATH = "/"

# Explicitly use the safe/default SameSite policy.
# This allows normal password-reset navigation from an email.
SESSION_COOKIE_SAMESITE = "Lax"

# Local development uses HTTP.
SESSION_COOKIE_SECURE = (
    os.getenv(
        "SESSION_COOKIE_SECURE",
        "False",
    ).lower() == "true"
)

# Keep session cookies inaccessible to JavaScript.
SESSION_COOKIE_HTTPONLY = True


# Use a ProblemPool-specific CSRF cookie as well.
CSRF_COOKIE_NAME = "problempool_csrftoken"

CSRF_COOKIE_PATH = "/"

CSRF_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = (
    os.getenv(
        "CSRF_COOKIE_SECURE",
        "False",
    ).lower() == "true"
)

CSRF_COOKIE_HTTPONLY = False


# ============================================================
# OTHER SECURITY HEADERS
# ============================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = "same-origin"

X_FRAME_OPTIONS = "DENY"


# ============================================================
# INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # ProblemPool applications
    "accounts",
    "problems",
    "solutions",
    "teams",
    "projects",
    "notifications",
    "dashboard",
    "core",
    "comments",
    "tasks",
    "reputation",
    "search",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "problem_pool.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "notifications.context_processors.notification_context",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "problem_pool.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv(
            "DB_NAME",
            "problem_pool_db",
        ),
        "USER": os.getenv(
            "DB_USER",
            "root",
        ),
        "PASSWORD": os.getenv(
            "DB_PASSWORD",
            "",
        ),
        "HOST": os.getenv(
            "DB_HOST",
            "localhost",
        ),
        "PORT": os.getenv(
            "DB_PORT",
            "3306",
        ),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# AUTHENTICATION
# ============================================================

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailBackend",
]

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/"


# ============================================================
# EMAIL
# ============================================================

# Development email backend.
# Password-reset emails are printed in the terminal instead
# of being sent through an external email service.

EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
)

DEFAULT_FROM_EMAIL = "noreply@problempool.local"
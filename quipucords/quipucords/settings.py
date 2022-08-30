#
# Copyright (c) 2017-2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""
Django settings for quipucords project.

Generated by 'django-admin startproject' using Django 1.11.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import logging
import os
import random
import string
from pathlib import Path

from .featureflag import FeatureFlag

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).absolute().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

PRODUCTION = bool(os.environ.get("PRODUCTION", False))


def is_int(value):
    """Check if a value is convertable to int.

    :param value: The value to convert
    :returns: The int or None if not convertable
    """
    if isinstance(value, int):
        return True

    try:
        int(value)
        return True
    except ValueError:
        return False


def create_random_key():
    """Create a randomized string."""
    return "".join(
        [
            random.SystemRandom().choice(
                string.ascii_letters + string.digits + string.punctuation
            )
            for _ in range(50)
        ]
    )


QPC_SSH_CONNECT_TIMEOUT = os.environ.get("QPC_SSH_CONNECT_TIMEOUT", "60")
if not is_int(QPC_SSH_CONNECT_TIMEOUT):
    logger.error(
        'QPC_SSH_CONNECT_TIMEOUT "%s" not an int.' "Setting to default of 60.",
        QPC_SSH_CONNECT_TIMEOUT,
    )
    QPC_SSH_CONNECT_TIMEOUT = "60"

QPC_SSH_INSPECT_TIMEOUT = os.environ.get("QPC_SSH_INSPECT_TIMEOUT", "120")
if not is_int(QPC_SSH_INSPECT_TIMEOUT):
    logger.error(
        'QPC_SSH_INSPECT_TIMEOUT "%s" not an int.' "Setting to default of 120.",
        QPC_SSH_INSPECT_TIMEOUT,
    )
    QPC_SSH_INSPECT_TIMEOUT = "120"

QPC_SSH_CONNECT_TIMEOUT = int(QPC_SSH_CONNECT_TIMEOUT)
QPC_SSH_INSPECT_TIMEOUT = int(QPC_SSH_INSPECT_TIMEOUT)

NETWORK_INSPECT_JOB_TIMEOUT = os.getenv(
    "NETWORK_INSPECT_JOB_TIMEOUT", "10800"
)  # 3 hours
if not is_int(NETWORK_INSPECT_JOB_TIMEOUT):
    logger.error(
        'NETWORK_INSPECT_JOB_TIMEOUT "%s" not an int.' "Setting to default of 10800.",
        NETWORK_INSPECT_JOB_TIMEOUT,
    )
    NETWORK_INSPECT_JOB_TIMEOUT = "10800"

NETWORK_CONNECT_JOB_TIMEOUT = os.getenv(
    "NETWORK_CONNECT_JOB_TIMEOUT", "600"
)  # 10 minutes
if not is_int(NETWORK_CONNECT_JOB_TIMEOUT):
    logger.error(
        'NETWORK_CONNECT_JOB_TIMEOUT "%s" not an int.' "Setting to default of 600.",
        NETWORK_CONNECT_JOB_TIMEOUT,
    )
    NETWORK_CONNECT_JOB_TIMEOUT = "600"

QPC_CONNECT_TASK_TIMEOUT = int(os.getenv("QPC_CONNECT_TASK_TIMEOUT", "30"))
QPC_INSPECT_TASK_TIMEOUT = int(os.getenv("QPC_INSPECT_TASK_TIMEOUT", "600"))

ANSIBLE_LOG_LEVEL = os.getenv("ANSIBLE_LOG_LEVEL", "0")
if not is_int(ANSIBLE_LOG_LEVEL):
    logger.error(
        'ANSIBLE_LOG_LEVEL "%s" not an int.' "Setting to default of 0.",
        ANSIBLE_LOG_LEVEL,
    )
    ANSIBLE_LOG_LEVEL = "0"

if PRODUCTION:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True

DJANGO_SECRET_PATH = Path(os.environ.get("DJANGO_SECRET_PATH", BASE_DIR / "secret.txt"))
if not DJANGO_SECRET_PATH.exists():
    SECRET_KEY = create_random_key()
    DJANGO_SECRET_PATH.write_text(SECRET_KEY, encoding="utf-8")
else:
    SECRET_KEY = DJANGO_SECRET_PATH.read_text(encoding="utf-8").strip()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", True)
if isinstance(DEBUG, str):
    DEBUG = DEBUG.lower() == "true"

ALLOWED_HOST_LIST = os.environ.get("DJANGO_ALLOWED_HOST_LIST", "*").split(",")
ALLOWED_HOSTS = ALLOWED_HOST_LIST

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "api",
]

if not PRODUCTION:
    INSTALLED_APPS.append("coverage")


MIDDLEWARE = [
    "api.common.middleware.ServerVersionMiddle",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "quipucords.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(os.path.dirname(__file__), "templates").replace("\\", "/"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LOGIN_REDIRECT_URL = "/client/"

WSGI_APPLICATION = "quipucords.wsgi.application"

DEFAULT_PAGINATION_CLASS = "api.common.pagination.StandardResultsSetPagination"

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": DEFAULT_PAGINATION_CLASS,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.user.authentication.QuipucordsExpiringTokenAuthentication",
    ),
}

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# Database Management System could be 'sqlite' or 'postgresql'
QPC_DBMS = os.getenv("QPC_DBMS", "postgres").lower()

if QPC_DBMS == "sqlite":
    # If user enters an invalid QPC_DBMS, use default postgresql
    DEV_DB = os.path.join(BASE_DIR, "db.sqlite3")
    PROD_DB = os.path.join(os.environ.get("DJANGO_DB_PATH", BASE_DIR), "db.sqlite3")
    DB_PATH = PROD_DB if PRODUCTION else DEV_DB
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DB_PATH,
            "TEST": {"NAME": ":memory:"},
        }
    }
else:
    QPC_DBMS = "postgres"
    # The following variables are only relevant when using a postgres database:
    QPC_DBMS_DATABASE = os.getenv("QPC_DBMS_DATABASE", "postgres")
    QPC_DBMS_USER = os.getenv("QPC_DBMS_USER", "postgres")
    QPC_DBMS_PASSWORD = os.getenv("QPC_DBMS_PASSWORD", "password")
    # In the following env variable, :: means localhost but allows IPv4
    #  and IPv6 connections
    # pylint: disable=invalid-envvar-default
    QPC_DBMS_HOST = os.getenv("QPC_DBMS_HOST", "localhost" or "::")
    QPC_DBMS_PORT = os.getenv("QPC_DBMS_PORT", 5432)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": QPC_DBMS_DATABASE,
            "USER": QPC_DBMS_USER,
            "PASSWORD": QPC_DBMS_PASSWORD,
            "HOST": QPC_DBMS_HOST,
            "PORT": QPC_DBMS_PORT,
        }
    }

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
NAME = "NAME"
USER_ATTRIBUTE_SIMILARITY_VALIDATOR = (
    "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
)
MINIMUM_LENGTH_VALIDATOR = (
    "django.contrib.auth.password_validation.MinimumLengthValidator"
)
COMMON_PASSWORD_VALIDATOR = (
    "django.contrib.auth.password_validation.CommonPasswordValidator"
)
NUMERIC_PASSWORD_VALIDATOR = (
    "django.contrib.auth.password_validation.NumericPasswordValidator"
)
AUTH_PASSWORD_VALIDATORS = [
    {
        NAME: USER_ATTRIBUTE_SIMILARITY_VALIDATOR,
    },
    {
        NAME: MINIMUM_LENGTH_VALIDATOR,
    },
    {
        NAME: COMMON_PASSWORD_VALIDATOR,
    },
    {
        NAME: NUMERIC_PASSWORD_VALIDATOR,
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATIC_URL = "/client/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "client"),
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

LOGGING_FORMATTER = os.getenv("DJANGO_LOG_FORMATTER", "simple")
DJANGO_LOGGING_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
QUIPUCORDS_LOGGING_LEVEL = os.getenv("QUIPUCORDS_LOG_LEVEL", "INFO")
LOGGING_HANDLERS = os.getenv("DJANGO_LOG_HANDLERS", "console").split(",")
VERBOSE_FORMATTING = (
    "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"
)

# pylint: disable=invalid-envvar-default
LOG_DIRECTORY = Path(os.getenv("LOG_DIRECTORY", BASE_DIR))
DEFAULT_LOG_FILE = LOG_DIRECTORY / "app.log"
LOGGING_FILE = Path(os.getenv("DJANGO_LOG_FILE", DEFAULT_LOG_FILE))
# pylint: enable=invalid-envvar-default

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": VERBOSE_FORMATTING},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": LOGGING_FORMATTER},
        "file": {
            "level": QUIPUCORDS_LOGGING_LEVEL,
            "class": "logging.FileHandler",
            "filename": LOGGING_FILE,
            "formatter": LOGGING_FORMATTER,
        },
    },
    "loggers": {
        "django": {
            "handlers": LOGGING_HANDLERS,
            "level": DJANGO_LOGGING_LEVEL,
        },
        "api.details_report": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.deployments_report": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.scan": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.scantask": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.scanjob": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.status": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "fingerprinter": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.signal.scanjob_signal": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.callback": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.manager": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.job": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.task": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.network": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.vcenter": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.satellite": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "quipucords.environment": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
    },
}

# Reverse default behavior to avoid host key checking
os.environ.setdefault("ANSIBLE_HOST_KEY_CHECKING", "False")


QPC_EXCLUDE_INTERNAL_FACTS = os.getenv("QPC_EXCLUDE_INTERNAL_FACTS", "True")
if isinstance(QPC_EXCLUDE_INTERNAL_FACTS, str):
    QPC_EXCLUDE_INTERNAL_FACTS = QPC_EXCLUDE_INTERNAL_FACTS.lower() == "true"

QPC_TOKEN_EXPIRE_HOURS = os.getenv("QPC_TOKEN_EXPIRE_HOURS", "24")
if is_int(QPC_TOKEN_EXPIRE_HOURS):
    QPC_TOKEN_EXPIRE_HOURS = int(QPC_TOKEN_EXPIRE_HOURS)

QPC_INSIGHTS_REPORT_SLICE_SIZE = os.getenv("QPC_INSIGHTS_REPORT_SLICE_SIZE", "10000")
if is_int(QPC_INSIGHTS_REPORT_SLICE_SIZE):
    QPC_INSIGHTS_REPORT_SLICE_SIZE = int(QPC_INSIGHTS_REPORT_SLICE_SIZE)

# Load Feature Flags
QPC_FEATURE_FLAGS = FeatureFlag()

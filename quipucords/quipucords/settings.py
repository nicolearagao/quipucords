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

import environ
from django.core.exceptions import ImproperlyConfigured

from .featureflag import FeatureFlag

logger = logging.getLogger(__name__)

env = environ.Env()

# BASE_DIR is ./quipucords/quipucords
BASE_DIR = Path(__file__).absolute().parent.parent
# DEFAULT_DATA_DIR is ./var, which is on .gitignore
DEFAULT_DATA_DIR = Path(env.str("QUIPUCORDS_DATA_DIR", BASE_DIR.parent / "var"))

PRODUCTION = env.bool("PRODUCTION", False)

# This suppresses warnings for models where an explicit primary key is not defined.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


class RelativePathnameFormatter(logging.Formatter):
    """Define a custom formatter to add a relative pathname."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record):
        """Add a relative_pathname attribute."""
        if Path(record.pathname).is_relative_to(BASE_DIR) is True:
            record.relative_pathname = Path(record.pathname).relative_to(BASE_DIR)
        else:
            record.relative_pathname = record.pathname
        return super().format(record)


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


def app_secret_key_and_path():
    """Return the SECRET_KEY and related DJANGO_SECRET_PATH to use."""
    # We need to support DJANGO_SECRET_KEY from the Environment.
    # This is necessary when the application keys are coming from
    # OpenShift project secrets through the environment.
    #
    # We also update the DJANGO_SECRET_PATH file accordingly
    # as it is also used as the Ansible password vault.
    django_secret_path = Path(
        env.str("DJANGO_SECRET_PATH", str(DEFAULT_DATA_DIR / "secret.txt"))
    )

    django_secret_key = env("DJANGO_SECRET_KEY", default=None)

    if django_secret_key:
        django_secret_path.write_text(django_secret_key, encoding="utf-8")
    elif not django_secret_path.exists():
        django_secret_key = create_random_key()
        django_secret_path.write_text(django_secret_key, encoding="utf-8")
    else:
        django_secret_key = django_secret_path.read_text(encoding="utf-8").strip()
    return django_secret_key, django_secret_path


QPC_SSH_CONNECT_TIMEOUT = env.int("QPC_SSH_CONNECT_TIMEOUT", 60)
QPC_SSH_INSPECT_TIMEOUT = env.int("QPC_SSH_INSPECT_TIMEOUT", 120)

NETWORK_INSPECT_JOB_TIMEOUT = env.int("NETWORK_INSPECT_JOB_TIMEOUT", 10800)  # 3 hours
NETWORK_CONNECT_JOB_TIMEOUT = env.int("NETWORK_CONNECT_JOB_TIMEOUT", 600)  # 10 minutes

QPC_CONNECT_TASK_TIMEOUT = env.int("QPC_CONNECT_TASK_TIMEOUT", 30)
QPC_INSPECT_TASK_TIMEOUT = env.int("QPC_INSPECT_TASK_TIMEOUT", 600)

QPC_HTTP_RETRY_MAX_NUMBER = env.int("QPC_HTTP_RETRY_MAX_NUMBER", 5)
QPC_HTTP_RETRY_BACKOFF = env.float("QPC_HTTP_RETRY_BACKOFF", 0.1)

ANSIBLE_LOG_LEVEL = env.int("ANSIBLE_LOG_LEVEL", 3)

if PRODUCTION:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SECRET_KEY, DJANGO_SECRET_PATH = app_secret_key_and_path()

# SECURITY WARNING: Running with DEBUG=True is a *BAD IDEA*, but this is unfortunately
# necessary because in some cases we still need to serve static files through Django.
# Please consider this note from the official Django docs:
# > This view will only work if DEBUG is True.
# > That’s because this view is grossly inefficient and probably insecure. This is only
# > intended for local development, and should never be used in production.
# TODO FIXME Remove this dangerous default.
DEBUG = env.bool("DJANGO_DEBUG", True)

if env.bool("QPC_URLLIB3_DISABLE_WARNINGS", False):
    # Optionally disable noisy urllib3 warnings.
    # Some scan target systems may have invalid or self-signed certs that the user does
    # not intend to fix, and they may optionally configure its source not to verify the
    # cert, but that makes urllib3 produce very noisy warnings that can drown out other
    # more meaningful log messages.
    import urllib3

    urllib3.disable_warnings()

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOST_LIST", default=["*"])
CORS_ALLOWED_ORIGIN_REGEXES = env.list(
    "DJANGO_CORS_ALLOWED_ORIGIN_REGEXES", default=[".*"]
)

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
    "corsheaders",
    "axes",  # django-axes
    "api",
]

if env.bool("QPC_ENABLE_DJANGO_EXTENSIONS", False):
    INSTALLED_APPS.append("django_extensions")

if not PRODUCTION:
    INSTALLED_APPS.append("coverage")

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend should be the first backend.
    "axes.backends.AxesStandaloneBackend",
    # Django ModelBackend is the default authentication backend.
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "api.common.middleware.ServerVersionMiddle",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    # It only formats user lockout messages and renders Axes lockout responses
    # on failed user authentication attempts from login views.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "quipucords.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [Path(__file__).parent / "templates"],
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

QUIPUCORDS_THROTTLE_RATE_ANON = env.str("QUIPUCORDS_THROTTLE_RATE_ANON", "2/second")
QUIPUCORDS_THROTTLE_RATE_USER = env.str("QUIPUCORDS_THROTTLE_RATE_USER", "20/second")
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": DEFAULT_PAGINATION_CLASS,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.user.authentication.QuipucordsExpiringTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": QUIPUCORDS_THROTTLE_RATE_ANON,
        "user": QUIPUCORDS_THROTTLE_RATE_USER,
    },
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_VERSION": "v1",
}

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# Database Management System could be 'sqlite' or 'postgresql'
QPC_DBMS = env.str("QPC_DBMS", "postgres").lower()
allowed_db_engines = ["sqlite", "postgres"]
if QPC_DBMS not in allowed_db_engines:
    raise ImproperlyConfigured(f"QPC_DBMS must be one of {allowed_db_engines}")

if QPC_DBMS == "sqlite":
    # If user enters an invalid QPC_DBMS, use default postgresql
    DEV_DB = DEFAULT_DATA_DIR / "db.sqlite3"
    PROD_DB = Path(env.str("DJANGO_DB_PATH", str(DEFAULT_DATA_DIR))) / "db.sqlite3"
    DB_PATH = PROD_DB if PRODUCTION else DEV_DB
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DB_PATH,
            "TEST": {"NAME": ":memory:"},
        }
    }
elif QPC_DBMS == "postgres":
    # The following variables are only relevant when using a postgres database:
    QPC_DBMS_DATABASE = env.str("QPC_DBMS_DATABASE", "qpc")
    QPC_DBMS_USER = env.str("QPC_DBMS_USER", "qpc")
    QPC_DBMS_PASSWORD = env.str("QPC_DBMS_PASSWORD", "qpc")
    QPC_DBMS_HOST = env.str("QPC_DBMS_HOST", "localhost")
    QPC_DBMS_PORT = env.int("QPC_DBMS_PORT", 5432)
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
QUIPUCORDS_BULK_CREATE_BATCH_SIZE = env.int("QUIPUCORDS_BULK_CREATE_BATCH_SIZE", 100)

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
VALIDATOR_MODULE = "django.contrib.auth.password_validation"
# Note: User.objects.make_random_password minimum length is 10 vs the default
#       for the MinimumLengthValidator is 8. let's declare it here for consistency.
QPC_MINIMUM_PASSWORD_LENGTH = 10
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": f"{VALIDATOR_MODULE}.UserAttributeSimilarityValidator",
    },
    {
        "NAME": f"{VALIDATOR_MODULE}.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": QPC_MINIMUM_PASSWORD_LENGTH,
        },
    },
    {
        "NAME": f"{VALIDATOR_MODULE}.CommonPasswordValidator",  # noqa: S105
    },
    {
        # Let's reject additional common passwords for Quipucords
        "NAME": f"{VALIDATOR_MODULE}.CommonPasswordValidator",  # noqa: S105
        "OPTIONS": {
            "password_list_path": BASE_DIR
            / ".."
            / "deploy"
            / "rejected_common_passwords.txt"
        },
    },
    {
        "NAME": f"{VALIDATOR_MODULE}.NumericPasswordValidator",  # noqa: S105
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

USE_I18N = True

USE_TZ = True
TIME_ZONE = "UTC"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = BASE_DIR / "staticfiles"

STATIC_URL = "/client/"

STATICFILES_DIRS = [BASE_DIR / "client"]

if not PRODUCTION:
    TESTDATA_DIR = BASE_DIR / "testdata"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}

LOGGING_FORMATTER = env.str("DJANGO_LOG_FORMATTER", "verbose")
DJANGO_LOGGING_LEVEL = env.str("DJANGO_LOG_LEVEL", "INFO")
CELERY_LOGGING_LEVEL = env.str("CELERY_LOGGING_LEVEL", "INFO")
QUIPUCORDS_LOGGING_LEVEL = env.str("QUIPUCORDS_LOG_LEVEL", "INFO")
LOGGING_HANDLERS = env.list("DJANGO_LOG_HANDLERS", default=["console"])
QUIPUCORDS_LOGGING_VERBOSE_FORMAT = env.str(
    "QUIPUCORDS_LOGGING_VERBOSE_FORMAT",
    "[%(levelname)s %(asctime)s pid=%(process)d tid=%(thread)d "
    "%(relative_pathname)s:%(funcName)s:%(lineno)d] %(message)s",
)
LOG_DIRECTORY = Path(env.str("QPC_LOG_DIRECTORY", str(DEFAULT_DATA_DIR / "logs")))
LOGGING_FILE = Path(env.str("DJANGO_LOG_FILE", str(LOG_DIRECTORY / "app.log")))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "()": RelativePathnameFormatter,
            "format": QUIPUCORDS_LOGGING_VERBOSE_FORMAT,
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
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
        "celery": {
            "handlers": LOGGING_HANDLERS,
            "level": CELERY_LOGGING_LEVEL,
            "propagate": False,
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
        "scanner": {
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
# Reverse default behavior for better readability in log files
os.environ.setdefault("ANSIBLE_NOCOLOR", "True")

QPC_EXCLUDE_INTERNAL_FACTS = env.bool("QPC_EXCLUDE_INTERNAL_FACTS", False)
QPC_TOKEN_EXPIRE_HOURS = env.int("QPC_TOKEN_EXPIRE_HOURS", 24)
QPC_INSIGHTS_REPORT_SLICE_SIZE = env.int("QPC_INSIGHTS_REPORT_SLICE_SIZE", 10000)
QPC_INSIGHTS_DATA_COLLECTOR_LABEL = env.str("QPC_INSIGHTS_DATA_COLLECTOR_LABEL", "qpc")

QPC_LOG_ALL_ENV_VARS_AT_STARTUP = env.bool("QPC_LOG_ALL_ENV_VARS_AT_STARTUP", True)

# Redis configuration

REDIS_USERNAME = env.str("REDIS_USERNAME", "")
REDIS_PASSWORD = env.str("REDIS_PASSWORD", "")
REDIS_HOST = env.str("REDIS_HOST", "localhost")
REDIS_PORT = env.int("REDIS_PORT", 6379)
REDIS_AUTH = f"{REDIS_USERNAME}:{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
REDIS_URL = f"redis://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}"

# Celery configuration

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", False)

# Axes configuration

# See also: https://django-axes.readthedocs.io/en/latest/4_configuration.html
AXES_ENABLED = env.bool("QUIPUCORDS_AXES_ENABLED", True)
AXES_FAILURE_LIMIT = env.int("QUIPUCORDS_AXES_FAILURE_LIMIT", 3)
AXES_LOCK_OUT_AT_FAILURE = env.bool("QUIPUCORDS_AXES_LOCK_OUT_AT_FAILURE", True)
AXES_COOLOFF_TIME = env.int("QUIPUCORDS_AXES_COOLOFF_TIME", 1)  # time in hours
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]

if not AXES_ENABLED or not AXES_LOCK_OUT_AT_FAILURE:
    logger.warning(
        "Account login failure lockout is DISABLED "
        "(QUIPUCORDS_AXES_ENABLED=%(AXES_ENABLED)s, "
        "QUIPUCORDS_AXES_LOCK_OUT_AT_FAILURE=%(AXES_LOCK_OUT_AT_FAILURE)s). "
        "This may be a security risk!",
        {
            "AXES_ENABLED": AXES_ENABLED,
            "AXES_LOCK_OUT_AT_FAILURE": AXES_LOCK_OUT_AT_FAILURE,
        },
    )

# Load Feature Flags
QPC_FEATURE_FLAGS = FeatureFlag()

# Enable or disable various behaviors
QPC_DISABLE_THREADED_SCAN_MANAGER = env.bool("QPC_DISABLE_THREADED_SCAN_MANAGER", False)
QPC_DISABLE_MULTIPROCESSING_SCAN_JOB_RUNNER = env.bool(
    "QPC_DISABLE_MULTIPROCESSING_SCAN_JOB_RUNNER", False
)
QPC_ENABLE_CELERY_SCAN_MANAGER = env.bool("QPC_ENABLE_CELERY_SCAN_MANAGER", False)

# Old hidden/buried configurations that should be removed or renamed
MAX_TIMEOUT_ORDERLY_SHUTDOWN = env.int("MAX_TIMEOUT_ORDERLY_SHUTDOWN", 30)
QUIPUCORDS_MANAGER_HEARTBEAT = env.int("QUIPUCORDS_MANAGER_HEARTBEAT", 60 * 15)

QUIPUCORDS_BYPASS_BUILD_CACHED_FINGERPRINTS = (
    False
    if PRODUCTION
    else env.bool("QUIPUCORDS_BYPASS_BUILD_CACHED_FINGERPRINTS", default=False)
)

# Defining both local memory and Redis as Django back-end caches.
#
# For now, we're keeping the default as local memory cache, this way
# the application will continue to work without the Celery scan manager enabled.
# Once quipucords only supports the Celery Scan Manager and Redis, we can then
# switch the default to be Redis.

# When enabling the Celery Scan Manager, we want to also enable the Redis
# Cache back-end. That can be disabled via QUIPUCORDS_ENABLE_REDIS_CACHE
# for development or testing purposes.

QUIPUCORDS_ENABLE_REDIS_CACHE = env.bool(
    "QUIPUCORDS_ENABLE_REDIS_CACHE", QPC_ENABLE_CELERY_SCAN_MANAGER
)

QPC_CACHE_TTL_DEFAULT = env.int("QPC_CACHE_TTL_DEFAULT", default=600)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "redis": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

if QUIPUCORDS_ENABLE_REDIS_CACHE:
    CACHES["redis"] = {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "discovery",
        "TIMEOUT": QPC_CACHE_TTL_DEFAULT,
    }

# Let's define various cache TTL's
QPC_SCAN_JOB_TTL = env.int("QPC_SCAN_JOB_TTL", default=24 * 3600)

QUIPUCORDS_CACHED_REPORTS_DATA_DIR = Path(
    env.str(
        "QUIPUCORDS_CACHED_REPORTS_DATA_DIR", str(DEFAULT_DATA_DIR / "cached_reports")
    )
)

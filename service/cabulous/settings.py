from datetime import timedelta

from cabulous.config import BASE_DIR, get_settings

settings = get_settings()

SECRET_KEY = settings.secret_key
DEBUG = settings.debug
ALLOWED_HOSTS = settings.allowed_hosts

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "authentication",
    "users",
    "common",
    "monitoring",
    "analytics",
    "communication",
]

if settings.minio.enabled:
    INSTALLED_APPS.append("storages")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cabulous.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
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

WSGI_APPLICATION = "cabulous.wsgi.application"
ASGI_APPLICATION = "cabulous.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": settings.database.engine,
        "NAME": settings.database.name,
        "USER": settings.database.user,
        "PASSWORD": settings.database.password,
        "HOST": settings.database.host,
        "PORT": settings.database.port,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = settings.time_zone

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": settings.redis.url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "cabulous",
    }
}

if settings.minio.enabled:
    AWS_ACCESS_KEY_ID = settings.minio.access_key
    AWS_SECRET_ACCESS_KEY = settings.minio.secret_key
    AWS_STORAGE_BUCKET_NAME = settings.minio.bucket_name
    AWS_S3_REGION_NAME = settings.minio.region_name
    AWS_S3_ENDPOINT_URL = settings.minio.endpoint_url
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_DEFAULT_ACL = settings.minio.default_acl
    AWS_QUERYSTRING_AUTH = settings.minio.querystring_auth
    AWS_S3_FILE_OVERWRITE = False
    AWS_LOCATION = "uploads"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = (
        f"{settings.minio.public_endpoint.rstrip('/')}/{settings.minio.bucket_name}/{AWS_LOCATION}/"
    )

JAZZMIN_SETTINGS = {
    "site_title": "Cabulous Admin",
    "site_header": "Cabulous",
    "site_brand": "Cabulous",
    "site_logo_classes": "img-circle",
    "welcome_sign": "Bem-vindo ao admin do Cabulous",
    "copyright": "Cabulous",
    "search_model": ["users.User"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "monitoring"],
}

CELERY_BROKER_URL = settings.celery.broker_url
CELERY_RESULT_BACKEND = settings.celery.result_backend
CELERY_TIMEZONE = settings.celery.timezone
CELERY_TASK_ALWAYS_EAGER = settings.celery.task_always_eager
CELERY_BEAT_SCHEDULE_FILENAME = settings.celery.beat_schedule_filename
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=settings.jwt.access_token_lifetime_minutes),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=settings.jwt.refresh_token_lifetime_days),
    "ROTATE_REFRESH_TOKENS": settings.jwt.rotate_refresh_tokens,
    "BLACKLIST_AFTER_ROTATION": settings.jwt.blacklist_after_rotation,
    "UPDATE_LAST_LOGIN": settings.jwt.update_last_login,
    "AUTH_HEADER_TYPES": tuple(settings.jwt.auth_header_types),
}

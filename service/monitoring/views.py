from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def healthcheck(_request: object) -> Response:
    database_ok = True
    redis_ok = True

    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError:
        database_ok = False

    try:
        cache.set("healthcheck", "ok", timeout=5)
        redis_ok = cache.get("healthcheck") == "ok"
    except Exception:
        redis_ok = False

    is_healthy = database_ok and redis_ok

    return Response(
        {
            "status": "ok" if is_healthy else "degraded",
            "services": {
                "database": database_ok,
                "redis": redis_ok,
            },
        },
        status=200 if is_healthy else 503,
    )

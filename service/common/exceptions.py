from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable."
    default_code = "service_unavailable"


class Conflict(APIException):
    status_code = 409
    default_detail = "Resource conflict, please retry."
    default_code = "conflict"

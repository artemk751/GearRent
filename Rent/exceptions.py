import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import set_rollback

logger = logging.getLogger(__name__)

ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "unsupported_media_type",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "server_error",
}

VALIDATION_MESSAGE = (
    "Передані дані некоректні. Перевірте поля в details та виправте помилки."
)


class ConflictError(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Операція суперечить поточному стану даних."
    default_code = "conflict"


def build_error(status_code, message, details=None):
    error = {
        "code": ERROR_CODES.get(status_code, "error"),
        "message": message,
    }
    if details:
        error["details"] = details
    return Response({"error": error}, status=status_code)


def _normalize_details(detail):
    if isinstance(detail, dict):
        return detail
    return {"non_field_errors": detail}


def api_exception_handler(exc, context):
    set_rollback()

    if isinstance(exc, (Http404, ObjectDoesNotExist)):
        return build_error(404, "Запитаний об'єкт не знайдено.")
    if isinstance(exc, ProtectedError):
        return build_error(
            409,
            "Неможливо видалити об'єкт, оскільки на нього посилаються інші записи.",
        )
    if isinstance(exc, IntegrityError):
        return build_error(
            409,
            "Операція порушує обмеження цілісності даних "
            "(наприклад, значення має бути унікальним).",
        )
    if isinstance(exc, exceptions.ValidationError):
        return build_error(400, VALIDATION_MESSAGE, _normalize_details(exc.detail))
    if isinstance(exc, exceptions.ParseError):
        return build_error(400, "Тіло запиту не є коректним JSON.")
    if isinstance(exc, exceptions.MethodNotAllowed):
        method = context["request"].method
        return build_error(405, f"Метод {method} не підтримується для цього ендпоінта.")
    if isinstance(exc, exceptions.UnsupportedMediaType):
        return build_error(415, "Підтримується лише Content-Type: application/json.")
    if isinstance(exc, exceptions.APIException):
        return build_error(exc.status_code, str(exc.detail))

    logger.exception("Необроблена помилка в API", exc_info=exc)
    return build_error(
        500, "Внутрішня помилка сервера. Спробуйте повторити запит пізніше."
    )

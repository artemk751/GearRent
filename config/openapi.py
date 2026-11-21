from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField(help_text="Машинозчитуваний код помилки.")
    message = serializers.CharField(help_text="Повідомлення українською.")
    details = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        required=False,
        help_text="Помилки по полях (лише для 400).",
    )


class ErrorSerializer(serializers.Serializer):
    error = ErrorBodySerializer()


def error_response(description):
    return OpenApiResponse(response=ErrorSerializer, description=description)


BAD_REQUEST = error_response("Некоректні дані запиту (див. `error.details`).")
UNAUTHORIZED = error_response(
    "Токен не передано, недійсний або прострочений. "
    "Заголовок: `Authorization: Bearer <access_token>`."
)
FORBIDDEN = error_response("Недостатньо прав (потрібна роль адміністратора).")
NOT_FOUND = error_response("Об'єкт не знайдено.")
CONFLICT = error_response("Конфлікт: дублікат назви або наявні пов'язані записи.")

UNAUTHORIZED_EXAMPLE = OpenApiExample(
    "Немає токена",
    value={
        "error": {
            "code": "unauthorized",
            "message": (
                "Потрібна автентифікація. Передайте токен у заголовку "
                "Authorization: Bearer <access_token>."
            ),
        }
    },
    response_only=True,
    status_codes=["401"],
)
FORBIDDEN_EXAMPLE = OpenApiExample(
    "Недостатньо прав",
    value={
        "error": {
            "code": "forbidden",
            "message": "Недостатньо прав для виконання цієї дії.",
        }
    },
    response_only=True,
    status_codes=["403"],
)


def not_found_example(message):
    return OpenApiExample(
        "Не знайдено",
        value={"error": {"code": "not_found", "message": message}},
        response_only=True,
        status_codes=["404"],
    )

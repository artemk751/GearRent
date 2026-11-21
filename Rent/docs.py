from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from config.openapi import (
    BAD_REQUEST,
    CONFLICT,
    FORBIDDEN,
    FORBIDDEN_EXAMPLE,
    NOT_FOUND,
    UNAUTHORIZED,
    UNAUTHORIZED_EXAMPLE,
    not_found_example,
)

PRODUCT_TAG = "Товари"
CATEGORY_TAG = "Категорії"
BRAND_TAG = "Бренди"

SORT_VALUES = [
    "id",
    "-id",
    "name",
    "-name",
    "price_per_day",
    "-price_per_day",
]


def id_parameter(description):
    return OpenApiParameter("pk", int, OpenApiParameter.PATH, description=description)


PRODUCT_REQUEST_EXAMPLE = OpenApiExample(
    "Новий товар",
    value={
        "name": "Намет 2-місний",
        "description": "Легкий намет для походів",
        "price_per_day": 250.0,
        "category_id": 1,
        "brand_id": 1,
        "is_available": True,
    },
    request_only=True,
)
PRODUCT_RESPONSE_EXAMPLE = OpenApiExample(
    "Товар",
    value={
        "id": 1,
        "name": "Намет 2-місний",
        "description": "Легкий намет для походів",
        "price_per_day": 250.0,
        "is_available": True,
        "category_id": 1,
        "category_name": "Намети",
        "brand_id": 1,
        "brand_name": "Husky",
    },
    response_only=True,
    status_codes=["200", "201"],
)
PRODUCT_VALIDATION_EXAMPLE = OpenApiExample(
    "Помилка валідації",
    value={
        "error": {
            "code": "bad_request",
            "message": (
                "Передані дані некоректні. Перевірте поля в details та виправте "
                "помилки."
            ),
            "details": {"price_per_day": ["Ціна за добу має бути більшою за 0."]},
        }
    },
    response_only=True,
    status_codes=["400"],
)

PRODUCT_FILTERS = [
    OpenApiParameter(
        "search",
        str,
        description="Пошук за назвою або описом (без урахування регістру).",
    ),
    OpenApiParameter("category_id", int, description="Фільтр за id категорії."),
    OpenApiParameter("brand_id", int, description="Фільтр за id бренду."),
    OpenApiParameter(
        "is_available",
        bool,
        description="Лише доступні (`true`/`1`) або недоступні (`false`/`0`) товари.",
    ),
    OpenApiParameter(
        "sort_by",
        str,
        enum=SORT_VALUES,
        description="Поле сортування; префікс `-` означає спадання.",
    ),
]


def product_list_docs(serializer):
    return {
        "get": extend_schema(
            tags=[PRODUCT_TAG],
            summary="Каталог товарів",
            description="Публічний ендпоінт: токен не потрібен.",
            parameters=PRODUCT_FILTERS,
            responses={
                200: serializer(many=True),
                400: BAD_REQUEST,
            },
            examples=[PRODUCT_RESPONSE_EXAMPLE],
            auth=[],
        ),
        "post": extend_schema(
            tags=[PRODUCT_TAG],
            summary="Додати товар",
            description="Потрібен токен авторизованого користувача.",
            request=serializer,
            responses={
                201: serializer,
                400: BAD_REQUEST,
                401: UNAUTHORIZED,
            },
            examples=[
                PRODUCT_REQUEST_EXAMPLE,
                PRODUCT_RESPONSE_EXAMPLE,
                PRODUCT_VALIDATION_EXAMPLE,
                UNAUTHORIZED_EXAMPLE,
            ],
        ),
    }


def product_detail_docs(serializer):
    pk = id_parameter("Ідентифікатор товару.")
    missing = not_found_example("Товар з id=999 не знайдено.")
    return {
        "get": extend_schema(
            tags=[PRODUCT_TAG],
            summary="Деталі товару",
            description="Публічний ендпоінт: токен не потрібен.",
            parameters=[pk],
            responses={200: serializer, 404: NOT_FOUND},
            examples=[PRODUCT_RESPONSE_EXAMPLE, missing],
            auth=[],
        ),
        "put": extend_schema(
            tags=[PRODUCT_TAG],
            summary="Повністю оновити товар",
            description=(
                "Потрібен токен авторизованого користувача. Усі обов'язкові поля."
            ),
            parameters=[pk],
            request=serializer,
            responses={
                200: serializer,
                400: BAD_REQUEST,
                401: UNAUTHORIZED,
                404: NOT_FOUND,
            },
            examples=[
                PRODUCT_REQUEST_EXAMPLE,
                PRODUCT_VALIDATION_EXAMPLE,
                UNAUTHORIZED_EXAMPLE,
                missing,
            ],
        ),
        "patch": extend_schema(
            tags=[PRODUCT_TAG],
            summary="Частково оновити товар",
            description=(
                "Потрібен токен авторизованого користувача. Усі поля необов'язкові."
            ),
            parameters=[pk],
            request=serializer,
            responses={
                200: serializer,
                400: BAD_REQUEST,
                401: UNAUTHORIZED,
                404: NOT_FOUND,
            },
            examples=[PRODUCT_VALIDATION_EXAMPLE, UNAUTHORIZED_EXAMPLE, missing],
        ),
        "delete": extend_schema(
            tags=[PRODUCT_TAG],
            summary="Видалити товар",
            description="Лише для адміністраторів (`is_staff`).",
            parameters=[pk],
            responses={
                204: OpenApiResponse(description="Товар видалено."),
                401: UNAUTHORIZED,
                403: FORBIDDEN,
                404: NOT_FOUND,
            },
            examples=[UNAUTHORIZED_EXAMPLE, FORBIDDEN_EXAMPLE, missing],
        ),
    }


def named_list_docs(tag, serializer, *, list_summary, create_summary):
    return {
        "get": extend_schema(
            tags=[tag],
            summary=list_summary,
            description="Публічний ендпоінт: токен не потрібен.",
            responses={200: serializer(many=True)},
            auth=[],
        ),
        "post": extend_schema(
            tags=[tag],
            summary=create_summary,
            description="Потрібен токен авторизованого користувача.",
            request=serializer,
            responses={
                201: serializer,
                400: BAD_REQUEST,
                401: UNAUTHORIZED,
                409: CONFLICT,
            },
            examples=[UNAUTHORIZED_EXAMPLE],
        ),
    }


def named_detail_docs(tag, serializer, *, label, retrieve, replace, update, delete):
    pk = id_parameter(f"Ідентифікатор: {label}.")
    return {
        "get": extend_schema(
            tags=[tag],
            summary=retrieve,
            description="Публічний ендпоінт: токен не потрібен.",
            parameters=[pk],
            responses={200: serializer, 404: NOT_FOUND},
            auth=[],
        ),
        "put": extend_schema(
            tags=[tag],
            summary=replace,
            description="Потрібен токен авторизованого користувача.",
            parameters=[pk],
            request=serializer,
            responses={
                200: serializer,
                400: BAD_REQUEST,
                401: UNAUTHORIZED,
                404: NOT_FOUND,
                409: CONFLICT,
            },
        ),
        "patch": extend_schema(
            tags=[tag],
            summary=update,
            description="Потрібен токен авторизованого користувача.",
            parameters=[pk],
            request=serializer,
            responses={
                200: serializer,
                400: BAD_REQUEST,
                401: UNAUTHORIZED,
                404: NOT_FOUND,
                409: CONFLICT,
            },
        ),
        "delete": extend_schema(
            tags=[tag],
            summary=delete,
            description=(
                "Лише для адміністраторів. Якщо за об'єктом закріплені товари, "
                "повертається 409."
            ),
            parameters=[pk],
            responses={
                204: OpenApiResponse(description="Видалено."),
                401: UNAUTHORIZED,
                403: FORBIDDEN,
                404: NOT_FOUND,
                409: CONFLICT,
            },
        ),
    }


def related_products_docs(tag, serializer, *, summary, label):
    return {
        "get": extend_schema(
            tags=[tag],
            summary=summary,
            description="Публічний ендпоінт: токен не потрібен.",
            parameters=[id_parameter(f"Ідентифікатор: {label}.")],
            responses={200: serializer(many=True), 404: NOT_FOUND},
            auth=[],
        ),
    }

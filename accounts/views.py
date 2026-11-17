import logging

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from config.openapi import (
    BAD_REQUEST,
    FORBIDDEN,
    FORBIDDEN_EXAMPLE,
    UNAUTHORIZED,
    UNAUTHORIZED_EXAMPLE,
    error_response,
)

from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    RefreshResponseSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)

AUTH_TAG = "Авторизація"
USERS_TAG = "Користувачі"


@extend_schema(
    tags=[AUTH_TAG],
    summary="Реєстрація",
    description=(
        "Створює користувача. Пароль зберігається лише у вигляді хеша. "
        "Токен не потрібен."
    ),
    request=RegisterSerializer,
    responses={201: UserSerializer, 400: BAD_REQUEST},
    examples=[
        OpenApiExample(
            "Запит",
            value={
                "username": "artem",
                "first_name": "Артем",
                "last_name": "К",
                "email": "artem@example.com",
                "password": "Str0ng!Pass-2026",
                "password_confirm": "Str0ng!Pass-2026",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Помилки валідації",
            value={
                "error": {
                    "code": "bad_request",
                    "message": (
                        "Передані дані некоректні. Перевірте поля в details та "
                        "виправте помилки."
                    ),
                    "details": {
                        "email": [
                            "Введіть коректну email-адресу, наприклад name@example.com."
                        ],
                        "password_confirm": ["Паролі не збігаються."],
                    },
                }
            },
            response_only=True,
            status_codes=["400"],
        ),
    ],
    auth=[],
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Зареєстровано користувача id=%s", user.pk)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=[AUTH_TAG],
    summary="Вхід",
    description=(
        "Повертає пару токенів і дані користувача. Access передається в заголовку "
        "`Authorization: Bearer <access>`."
    ),
    request=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: BAD_REQUEST,
        401: error_response("Невірне ім'я користувача або пароль."),
    },
    examples=[
        OpenApiExample(
            "Запит",
            value={"username": "artem", "password": "Str0ng!Pass-2026"},
            request_only=True,
        ),
        OpenApiExample(
            "Невірний пароль",
            value={
                "error": {
                    "code": "unauthorized",
                    "message": "Невірне ім'я користувача або пароль.",
                }
            },
            response_only=True,
            status_codes=["401"],
        ),
    ],
    auth=[],
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        logger.info("Успішний вхід: user_id=%s", response.data["user"]["id"])
        return response


@extend_schema(
    tags=[AUTH_TAG],
    summary="Оновлення access-токена",
    description=(
        "Приймає refresh-токен і повертає новий access (та новий refresh, бо "
        "ввімкнено ротацію). Викликається, коли access закінчився (відповідь 401)."
    ),
    responses={
        200: RefreshResponseSerializer,
        400: BAD_REQUEST,
        401: error_response("Refresh-токен недійсний або прострочений."),
    },
    examples=[
        OpenApiExample(
            "Запит",
            value={"refresh": "<refresh_token>"},
            request_only=True,
        ),
    ],
    auth=[],
)
class RefreshView(TokenRefreshView):
    pass


@extend_schema(
    tags=[USERS_TAG],
    summary="Мій профіль",
    description="Дані поточного користувача. Потрібен токен.",
    responses={200: UserSerializer, 401: UNAUTHORIZED},
    examples=[UNAUTHORIZED_EXAMPLE],
)
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=[USERS_TAG],
    summary="Список користувачів",
    description="Лише для адміністраторів (`is_staff`).",
    responses={200: UserSerializer(many=True), 401: UNAUTHORIZED, 403: FORBIDDEN},
    examples=[UNAUTHORIZED_EXAMPLE, FORBIDDEN_EXAMPLE],
)
class UserListView(generics.ListAPIView):
    queryset = User.objects.order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None

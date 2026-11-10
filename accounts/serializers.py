from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

USERNAME_MAX = 30
NAME_MAX = 30
EMAIL_MAX = 254
PASSWORD_MIN = 8
PASSWORD_MAX = 128


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=USERNAME_MAX,
        validators=[
            User.username_validator,
            UniqueValidator(
                queryset=User.objects.all(),
                lookup="iexact",
                message="Користувач з таким іменем уже існує.",
            ),
        ],
    )
    first_name = serializers.CharField(
        max_length=NAME_MAX, required=False, allow_blank=True, default=""
    )
    last_name = serializers.CharField(
        max_length=NAME_MAX, required=False, allow_blank=True, default=""
    )
    email = serializers.EmailField(
        max_length=EMAIL_MAX,
        error_messages={
            "invalid": "Введіть коректну email-адресу, наприклад name@example.com."
        },
    )
    password = serializers.CharField(
        write_only=True,
        min_length=PASSWORD_MIN,
        max_length=PASSWORD_MAX,
        trim_whitespace=False,
        style={"input_type": "password"},
        error_messages={
            "min_length": f"Пароль має містити щонайменше {PASSWORD_MIN} символів."
        },
    )
    password_confirm = serializers.CharField(
        write_only=True,
        max_length=PASSWORD_MAX,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        value = value.strip().lower()
        if "." not in value.rsplit("@", 1)[-1]:
            raise serializers.ValidationError(
                "Введіть коректну email-адресу, наприклад name@example.com."
            )
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Користувач з такою email-адресою вже існує."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Паролі не збігаються."}
            )
        candidate = User(
            username=attrs.get("username", ""),
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Невірне ім'я користувача або пароль."
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

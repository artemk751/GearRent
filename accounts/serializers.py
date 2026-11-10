from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
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
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=PASSWORD_MIN,
        max_length=PASSWORD_MAX,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        max_length=PASSWORD_MAX,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "password_confirm",
        )
        extra_kwargs = {
            "username": {"max_length": USERNAME_MAX},
            "first_name": {"required": False, "allow_blank": True, "max_length": NAME_MAX},
            "last_name": {"required": False, "allow_blank": True, "max_length": NAME_MAX},
            "email": {"required": True, "allow_blank": False, "max_length": EMAIL_MAX},
        }

    def validate_email(self, value):
        value = value.strip().lower()
        domain = value.rsplit("@", 1)[-1]
        if "." not in domain:
            raise serializers.ValidationError("Enter a valid email address, e.g. name@example.com.")
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        candidate = User(
            username=attrs.get("username", ""),
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {"no_active_account": "Invalid username or password."}
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

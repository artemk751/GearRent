from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

User = get_user_model()

PASSWORD = "Str0ng!Pass-2026"

VALID = {
    "username": "artem",
    "first_name": "Artem",
    "last_name": "K",
    "email": "artem@example.com",
    "password": PASSWORD,
    "password_confirm": PASSWORD,
}


class RegisterTests(APITestCase):
    def register(self, **changes):
        return self.client.post(
            reverse("register"), {**VALID, **changes}, format="json"
        )

    def assert_field_error(self, response, field):
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "bad_request")
        self.assertIn(field, error["details"])

    def test_success_and_password_is_hashed(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.json())
        user = User.objects.get(username="artem")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff)

    def test_names_are_optional(self):
        data = {k: v for k, v in VALID.items() if k not in ("first_name", "last_name")}
        response = self.client.post(reverse("register"), data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_required_fields(self):
        response = self.client.post(reverse("register"), {}, format="json")
        for field in ("username", "email", "password", "password_confirm"):
            self.assert_field_error(response, field)

    def test_invalid_email(self):
        for bad in ("not-an-email", "a@b", "@example.com"):
            self.assert_field_error(self.register(email=bad), "email")

    def test_max_length(self):
        self.assert_field_error(self.register(username="u" * 31), "username")
        self.assert_field_error(self.register(first_name="n" * 31), "first_name")
        self.assert_field_error(self.register(last_name="n" * 31), "last_name")

    def test_short_password(self):
        response = self.register(password="Ab1!", password_confirm="Ab1!")
        self.assert_field_error(response, "password")

    def test_weak_password(self):
        for weak in ("12345678", "password123"):
            response = self.register(password=weak, password_confirm=weak)
            self.assert_field_error(response, "password")

    def test_password_mismatch(self):
        response = self.register(password_confirm="Other!Pass-2026")
        self.assert_field_error(response, "password_confirm")

    def test_duplicate_username_and_email(self):
        self.assertEqual(self.register().status_code, 201)
        response = self.register(email="other@example.com")
        self.assert_field_error(response, "username")
        response = self.register(username="other", email="ARTEM@example.com")
        self.assert_field_error(response, "email")

    def test_invalid_token_in_header_does_not_break_registration(self):
        response = self.client.post(
            reverse("register"),
            VALID,
            format="json",
            HTTP_AUTHORIZATION="Bearer broken",
        )
        self.assertEqual(response.status_code, 201)


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("artem", "artem@example.com", PASSWORD)

    def login(self, username="artem", password=PASSWORD):
        return self.client.post(
            reverse("login"),
            {"username": username, "password": password},
            format="json",
        )

    def bearer(self, access):
        return {"HTTP_AUTHORIZATION": f"Bearer {access}"}

    def test_login_returns_tokens_and_user(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user"]["username"], "artem")
        self.assertNotIn("password", data["user"])

    def test_login_wrong_password_is_401(self):
        response = self.login(password="wrong")
        self.assertEqual(response.status_code, 401)
        error = response.json()["error"]
        self.assertEqual(error["code"], "unauthorized")
        self.assertEqual(error["message"], "Невірне ім'я користувача або пароль.")

    def test_login_missing_fields_is_400(self):
        response = self.client.post(reverse("login"), {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json()["error"]["details"])

    def test_refresh_returns_new_access(self):
        refresh = self.login().json()["refresh"]
        response = self.client.post(
            reverse("token-refresh"), {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_refresh_with_invalid_token_is_401(self):
        response = self.client.post(
            reverse("token-refresh"), {"refresh": "broken"}, format="json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "unauthorized")

    def test_me_requires_token(self):
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "unauthorized")

    def test_me_with_invalid_token_is_401(self):
        response = self.client.get(reverse("me"), **self.bearer("broken"))
        self.assertEqual(response.status_code, 401)

    def test_me_with_token(self):
        access = self.login().json()["access"]
        response = self.client.get(reverse("me"), **self.bearer(access))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "artem@example.com")

    def test_user_list_is_admin_only(self):
        self.assertEqual(self.client.get(reverse("user-list")).status_code, 401)

        access = self.login().json()["access"]
        response = self.client.get(reverse("user-list"), **self.bearer(access))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "forbidden")

        User.objects.create_superuser("admin", "admin@example.com", PASSWORD)
        admin_access = self.login("admin").json()["access"]
        response = self.client.get(reverse("user-list"), **self.bearer(admin_access))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

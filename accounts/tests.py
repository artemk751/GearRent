from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER = "/api/auth/register/"
LOGIN = "/api/auth/login/"
REFRESH = "/api/auth/token/refresh/"
ME = "/api/auth/me/"
USERS = "/api/auth/users/"

VALID = {
    "username": "artem",
    "first_name": "Artem",
    "last_name": "K",
    "email": "artem@example.com",
    "password": "Str0ng!Pass-2026",
    "password_confirm": "Str0ng!Pass-2026",
}


class RegisterTests(APITestCase):
    def test_success_and_password_is_hashed(self):
        r = self.client.post(REGISTER, VALID, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("password", r.data)
        user = User.objects.get(username="artem")
        self.assertNotEqual(user.password, VALID["password"])
        self.assertTrue(user.check_password(VALID["password"]))

    def test_names_optional(self):
        data = {k: v for k, v in VALID.items() if k not in ("first_name", "last_name")}
        self.assertEqual(self.client.post(REGISTER, data, format="json").status_code, 201)

    def test_required_fields(self):
        r = self.client.post(REGISTER, {}, format="json")
        self.assertEqual(r.status_code, 400)
        for field in ("username", "email", "password", "password_confirm"):
            self.assertIn(field, r.data)

    def test_invalid_email(self):
        for bad in ("not-an-email", "a@b", "@example.com"):
            r = self.client.post(REGISTER, {**VALID, "email": bad}, format="json")
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn("email", r.data)

    def test_max_length(self):
        r = self.client.post(REGISTER, {**VALID, "username": "u" * 31}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("username", r.data)

    def test_short_password(self):
        r = self.client.post(
            REGISTER, {**VALID, "password": "Ab1!", "password_confirm": "Ab1!"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("password", r.data)

    def test_weak_password(self):
        for weak in ("12345678", "password123"):
            r = self.client.post(
                REGISTER, {**VALID, "password": weak, "password_confirm": weak}, format="json"
            )
            self.assertEqual(r.status_code, 400, weak)
            self.assertIn("password", r.data)

    def test_password_mismatch(self):
        r = self.client.post(REGISTER, {**VALID, "password_confirm": "Other!Pass-2026"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("password_confirm", r.data)

    def test_duplicates(self):
        self.client.post(REGISTER, VALID, format="json")
        r = self.client.post(REGISTER, {**VALID, "email": "other@example.com"}, format="json")
        self.assertIn("username", r.data)
        r = self.client.post(
            REGISTER, {**VALID, "username": "other", "email": "ARTEM@example.com"}, format="json"
        )
        self.assertIn("email", r.data)


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("artem", "artem@example.com", "Str0ng!Pass-2026")

    def login(self, password="Str0ng!Pass-2026"):
        return self.client.post(LOGIN, {"username": "artem", "password": password}, format="json")

    def test_login_returns_tokens_and_user(self):
        r = self.login()
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)
        self.assertEqual(r.data["user"]["username"], "artem")

    def test_login_wrong_password(self):
        r = self.login("wrong")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.data["detail"], "Invalid username or password.")

    def test_refresh(self):
        refresh = self.login().data["refresh"]
        r = self.client.post(REFRESH, {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get(ME).status_code, 401)
        access = self.login().data["access"]
        r = self.client.get(ME, HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["email"], "artem@example.com")

    def test_admin_only_endpoint(self):
        self.assertEqual(self.client.get(USERS).status_code, 401)
        access = self.login().data["access"]
        r = self.client.get(USERS, HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(r.status_code, 403)

        User.objects.create_superuser("admin", "admin@example.com", "Adm1n!Pass-2026")
        r = self.client.post(LOGIN, {"username": "admin", "password": "Adm1n!Pass-2026"}, format="json")
        r = self.client.get(USERS, HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        self.assertEqual(r.status_code, 200)

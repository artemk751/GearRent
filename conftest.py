from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from rent.models import Brand, Category, Product

User = get_user_model()

USER_PASSWORD = "Us3r!Pass-2026"
ADMIN_PASSWORD = "Adm1n!Pass-2026"


@pytest.fixture
def user_password():
    return USER_PASSWORD


@pytest.fixture
def regular_user(db):
    return User.objects.create_user("user", "user@example.com", USER_PASSWORD)


@pytest.fixture
def admin_account(db):
    return User.objects.create_superuser("admin", "admin@example.com", ADMIN_PASSWORD)


@pytest.fixture
def anon_client():

    return APIClient()


@pytest.fixture
def user_client(regular_user):

    client = APIClient()
    client.force_authenticate(regular_user)
    return client


@pytest.fixture
def admin_api_client(admin_account):

    client = APIClient()
    client.force_authenticate(admin_account)
    return client


@pytest.fixture
def login(anon_client):

    def _login(username, password):
        return anon_client.post(
            reverse("login"),
            {"username": username, "password": password},
            format="json",
        )

    return _login


@pytest.fixture
def category(db):
    return Category.objects.create(name="Tents", description="Намети")


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="Husky")


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Tent Husky 2P",
        description="Легкий намет",
        price_per_day=Decimal("250.00"),
    )


@pytest.fixture
def catalog(category, brand):

    backpacks = Category.objects.create(name="Backpacks")
    osprey = Brand.objects.create(name="Osprey")
    return [
        Product.objects.create(
            category=category,
            brand=brand,
            name="Tent Husky 2P",
            description="Light tent",
            price_per_day=Decimal("250.00"),
        ),
        Product.objects.create(
            category=backpacks,
            brand=osprey,
            name="Backpack Osprey 60",
            description="Hiking pack",
            price_per_day=Decimal("180.00"),
        ),
        Product.objects.create(
            category=backpacks,
            brand=osprey,
            name="Backpack Osprey 30",
            description="Day pack",
            price_per_day=Decimal("90.00"),
            is_available=False,
        ),
    ]


@pytest.fixture
def product_payload(category, brand):

    return {
        "name": "Backpack",
        "description": "60 л",
        "price_per_day": 180,
        "category_id": category.id,
        "brand_id": brand.id,
        "is_available": True,
    }

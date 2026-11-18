import json

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def schema(anon_client):
    response = anon_client.get(reverse("schema"), {"format": "json"})
    assert response.status_code == 200
    return json.loads(response.content)


def test_schema_describes_main_endpoints(schema):
    paths = schema["paths"]
    for path in (
        "/api/v1/products",
        "/api/v1/categories",
        "/api/v1/brands",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/users/me",
        "/api/v1/users",
    ):
        assert path in paths, path


def test_products_collection_documents_methods_and_filters(schema):
    operations = schema["paths"]["/api/v1/products"]
    assert set(operations) >= {"get", "post"}
    params = {p["name"] for p in operations["get"]["parameters"]}
    assert params == {"search", "category_id", "brand_id", "is_available", "sort_by"}
    assert {"200", "400"} <= set(operations["get"]["responses"])
    assert {"201", "400", "401"} <= set(operations["post"]["responses"])


def test_product_detail_documents_all_methods(schema):
    prefix = "/api/v1/products/"
    detail_paths = [
        p for p in schema["paths"] if p.startswith(prefix) and "/" not in p[len(prefix) :]
    ]
    assert len(detail_paths) == 1
    operations = schema["paths"][detail_paths[0]]
    assert set(operations) >= {"get", "put", "patch", "delete"}
    assert {"204", "401", "403", "404"} <= set(operations["delete"]["responses"])


def test_protected_operations_require_bearer_token(schema):
    assert schema["components"]["securitySchemes"]
    operations = schema["paths"]["/api/v1/products"]
    assert operations["post"]["security"]
    assert not operations["get"].get("security")


def test_swagger_ui_and_redoc_are_served(anon_client):
    swagger = anon_client.get(reverse("swagger-ui"))
    assert swagger.status_code == 200
    assert "text/html" in swagger["Content-Type"]
    redoc = anon_client.get(reverse("redoc"))
    assert redoc.status_code == 200

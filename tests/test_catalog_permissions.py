import pytest
from django.urls import reverse

from rent.models import Brand, Category

pytestmark = pytest.mark.django_db

RESOURCES = [
    pytest.param("category", Category, id="categories"),
    pytest.param("brand", Brand, id="brands"),
]


@pytest.mark.parametrize(("prefix", "model"), RESOURCES)
class TestNamedResources:
    def list_url(self, prefix):
        return reverse(f"{prefix}-list")

    def detail_url(self, prefix, pk):
        return reverse(f"{prefix}-detail", args=[pk])

    def test_anonymous_can_read(self, anon_client, prefix, model, category, brand):
        assert anon_client.get(self.list_url(prefix)).status_code == 200
        obj = model.objects.first()
        assert anon_client.get(self.detail_url(prefix, obj.pk)).status_code == 200

    def test_anonymous_cannot_create(self, anon_client, prefix, model):
        response = anon_client.post(
            self.list_url(prefix), {"name": "Новий"}, format="json"
        )
        assert response.status_code == 401
        assert model.objects.count() == 0

    def test_user_can_create_and_update(self, user_client, prefix, model):
        created = user_client.post(
            self.list_url(prefix), {"name": "Alpha"}, format="json"
        )
        assert created.status_code == 201
        pk = created.json()["id"]

        updated = user_client.patch(
            self.detail_url(prefix, pk), {"description": "Опис"}, format="json"
        )
        assert updated.status_code == 200
        assert model.objects.get(pk=pk).description == "Опис"

    def test_blank_name_is_400(self, user_client, prefix, model):
        response = user_client.post(self.list_url(prefix), {"name": ""}, format="json")
        assert response.status_code == 400
        assert "name" in response.json()["error"]["details"]

    def test_duplicate_name_is_409(self, user_client, prefix, model, category, brand):
        existing = model.objects.first()
        response = user_client.post(
            self.list_url(prefix), {"name": existing.name}, format="json"
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "conflict"

    def test_user_cannot_delete(self, user_client, prefix, model, category, brand):
        obj = model.objects.first()
        response = user_client.delete(self.detail_url(prefix, obj.pk))
        assert response.status_code == 403
        assert model.objects.filter(pk=obj.pk).exists()

    def test_admin_can_delete_empty_object(self, admin_api_client, prefix, model):
        obj = model.objects.create(name="Порожній")
        response = admin_api_client.delete(self.detail_url(prefix, obj.pk))
        assert response.status_code == 204
        assert not model.objects.filter(pk=obj.pk).exists()

    def test_cannot_delete_object_with_products(
        self, admin_api_client, prefix, model, product
    ):
        obj = getattr(product, prefix)
        response = admin_api_client.delete(self.detail_url(prefix, obj.pk))
        assert response.status_code == 409
        assert "1 товар" in response.json()["error"]["message"]
        assert model.objects.filter(pk=obj.pk).exists()

    def test_related_products(self, anon_client, prefix, model, product):
        obj = getattr(product, prefix)
        response = anon_client.get(reverse(f"{prefix}-products", args=[obj.pk]))
        assert response.status_code == 200
        assert [p["id"] for p in response.json()] == [product.id]

    def test_related_products_of_missing_object_is_404(
        self, anon_client, prefix, model
    ):
        response = anon_client.get(reverse(f"{prefix}-products", args=[999]))
        assert response.status_code == 404

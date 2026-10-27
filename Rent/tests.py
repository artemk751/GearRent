from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Brand, Category, Product


class ApiTestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Намети")
        self.brand = Brand.objects.create(name="Husky")
        self.product = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name="Намет 2-місний",
            description="Легкий намет",
            price_per_day=Decimal("250.00"),
        )

    def assert_error(self, response, status_code, code):
        self.assertEqual(response.status_code, status_code)
        body = response.json()
        self.assertEqual(list(body.keys()), ["error"])
        self.assertEqual(body["error"]["code"], code)
        self.assertTrue(body["error"]["message"])

    def product_payload(self, **changes):
        payload = {
            "name": "Рюкзак",
            "description": "60 л",
            "price_per_day": 180,
            "category_id": self.category.id,
            "brand_id": self.brand.id,
        }
        payload.update(changes)
        return payload


class CategoryApiTests(ApiTestCase):
    def test_list(self):
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["name"], "Намети")

    def test_create(self):
        response = self.client.post(
            reverse("category-list"), {"name": "Альпінізм"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "Альпінізм")
        self.assertTrue(Category.objects.filter(name="Альпінізм").exists())

    def test_create_blank_name_is_400(self):
        response = self.client.post(
            reverse("category-list"), {"name": ""}, format="json"
        )
        self.assert_error(response, 400, "bad_request")
        self.assertIn("name", response.json()["error"]["details"])

    def test_create_missing_name_is_400(self):
        response = self.client.post(reverse("category-list"), {}, format="json")
        self.assert_error(response, 400, "bad_request")

    def test_create_duplicate_is_409(self):
        response = self.client.post(
            reverse("category-list"), {"name": "намети"}, format="json"
        )
        self.assert_error(response, 409, "conflict")
        self.assertEqual(Category.objects.count(), 1)

    def test_retrieve(self):
        url = reverse("category-detail", args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.category.id)

    def test_retrieve_missing_is_404(self):
        response = self.client.get(reverse("category-detail", args=[999]))
        self.assert_error(response, 404, "not_found")

    def test_put_updates(self):
        url = reverse("category-detail", args=[self.category.id])
        response = self.client.put(url, {"name": "Намети та тенти"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Намети та тенти")

    def test_put_same_name_is_allowed(self):
        url = reverse("category-detail", args=[self.category.id])
        response = self.client.put(url, {"name": "Намети"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_patch_updates_description_only(self):
        url = reverse("category-detail", args=[self.category.id])
        response = self.client.patch(url, {"description": "Туристичні"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Намети")
        self.assertEqual(self.category.description, "Туристичні")

    def test_delete_category_with_products_is_409(self):
        url = reverse("category-detail", args=[self.category.id])
        response = self.client.delete(url)
        self.assert_error(response, 409, "conflict")
        self.assertIn("1 товар", response.json()["error"]["message"])
        self.assertTrue(Category.objects.filter(pk=self.category.id).exists())

    def test_delete_empty_category(self):
        empty = Category.objects.create(name="Порожня")
        response = self.client.delete(reverse("category-detail", args=[empty.id]))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(pk=empty.id).exists())

    def test_category_products(self):
        url = reverse("category-products", args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_category_products_missing_category_is_404(self):
        response = self.client.get(reverse("category-products", args=[999]))
        self.assert_error(response, 404, "not_found")


class BrandApiTests(ApiTestCase):
    def test_crud_flow(self):
        created = self.client.post(
            reverse("brand-list"), {"name": "Osprey"}, format="json"
        )
        self.assertEqual(created.status_code, 201)
        url = reverse("brand-detail", args=[created.json()["id"]])
        self.assertEqual(self.client.get(url).status_code, 200)
        updated = self.client.put(url, {"name": "Osprey Packs"}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assert_error(self.client.get(url), 404, "not_found")

    def test_duplicate_is_409(self):
        response = self.client.post(
            reverse("brand-list"), {"name": "HUSKY"}, format="json"
        )
        self.assert_error(response, 409, "conflict")

    def test_delete_brand_with_products_is_409(self):
        response = self.client.delete(reverse("brand-detail", args=[self.brand.id]))
        self.assert_error(response, 409, "conflict")
        self.assertIn("Husky", response.json()["error"]["message"])

    def test_brand_products(self):
        response = self.client.get(reverse("brand-products", args=[self.brand.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class ProductApiTests(ApiTestCase):
    def test_list_and_detail(self):
        listing = self.client.get(reverse("product-list"))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()[0]["price_per_day"], 250.0)
        detail = self.client.get(reverse("product-detail", args=[self.product.id]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["category_name"], "Намети")
        self.assertEqual(detail.json()["brand_name"], "Husky")

    def test_create(self):
        response = self.client.post(
            reverse("product-list"), self.product_payload(), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "Рюкзак")
        self.assertEqual(Product.objects.count(), 2)

    def test_create_invalid_price_is_400(self):
        for price in (0, -5, "abc"):
            response = self.client.post(
                reverse("product-list"),
                self.product_payload(price_per_day=price),
                format="json",
            )
            self.assert_error(response, 400, "bad_request")
            self.assertIn("price_per_day", response.json()["error"]["details"])

    def test_create_unknown_category_is_400(self):
        response = self.client.post(
            reverse("product-list"),
            self.product_payload(category_id=999),
            format="json",
        )
        self.assert_error(response, 400, "bad_request")
        self.assertIn("category_id", response.json()["error"]["details"])

    def test_create_missing_fields_is_400(self):
        response = self.client.post(
            reverse("product-list"), {"name": "Тільки назва"}, format="json"
        )
        self.assert_error(response, 400, "bad_request")
        details = response.json()["error"]["details"]
        for field in ("price_per_day", "category_id", "brand_id"):
            self.assertIn(field, details)

    def test_create_malformed_json_is_400(self):
        response = self.client.post(
            reverse("product-list"),
            data="{не json",
            content_type="application/json",
        )
        self.assert_error(response, 400, "bad_request")

    def test_create_wrong_content_type_is_415(self):
        response = self.client.post(
            reverse("product-list"),
            data="name=x",
            content_type="text/plain",
        )
        self.assert_error(response, 415, "unsupported_media_type")

    def test_put_updates(self):
        url = reverse("product-detail", args=[self.product.id])
        response = self.client.put(
            url,
            self.product_payload(name="Намет Pro", price_per_day=300),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Намет Pro")
        self.assertEqual(self.product.price_per_day, Decimal("300.00"))

    def test_patch_updates_availability(self):
        url = reverse("product-detail", args=[self.product.id])
        response = self.client.patch(url, {"is_available": False}, format="json")
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_available)

    def test_missing_product_is_404(self):
        url = reverse("product-detail", args=[999])
        for method in (
            self.client.get,
            self.client.delete,
        ):
            self.assert_error(method(url), 404, "not_found")
        response = self.client.put(url, self.product_payload(), format="json")
        self.assert_error(response, 404, "not_found")

    def test_delete(self):
        url = reverse("product-detail", args=[self.product.id])
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Product.objects.exists())

    def test_method_not_allowed_is_405(self):
        response = self.client.delete(reverse("product-list"))
        self.assert_error(response, 405, "method_not_allowed")

    def test_unknown_endpoint_is_json_404(self):
        response = self.client.get("/api/v1/unknown")
        self.assert_error(response, 404, "not_found")


class ProductFilterTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.other_category = Category.objects.create(name="Рюкзаки")
        self.other_brand = Brand.objects.create(name="Osprey")
        self.backpack = Product.objects.create(
            category=self.other_category,
            brand=self.other_brand,
            name="Рюкзак 60 л",
            price_per_day=Decimal("100.00"),
            is_available=False,
        )

    def names(self, **params):
        response = self.client.get(reverse("product-list"), params)
        self.assertEqual(response.status_code, 200)
        return [item["name"] for item in response.json()]

    def test_search(self):
        self.assertEqual(self.names(search="Рюкзак"), ["Рюкзак 60 л"])

    def test_filter_by_category_and_brand(self):
        self.assertEqual(self.names(category_id=self.category.id), ["Намет 2-місний"])
        self.assertEqual(self.names(brand_id=self.other_brand.id), ["Рюкзак 60 л"])

    def test_filter_by_availability(self):
        self.assertEqual(self.names(is_available="false"), ["Рюкзак 60 л"])

    def test_sort_by_price(self):
        self.assertEqual(
            self.names(sort_by="price_per_day"),
            ["Рюкзак 60 л", "Намет 2-місний"],
        )
        self.assertEqual(
            self.names(sort_by="-price_per_day"),
            ["Намет 2-місний", "Рюкзак 60 л"],
        )

    def test_invalid_params_are_400(self):
        for params in (
            {"category_id": "abc"},
            {"brand_id": "x"},
            {"is_available": "maybe"},
            {"sort_by": "color"},
        ):
            response = self.client.get(reverse("product-list"), params)
            self.assert_error(response, 400, "bad_request")

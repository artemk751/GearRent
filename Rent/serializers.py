from decimal import Decimal

from rest_framework import serializers

from .exceptions import ConflictError
from .models import Brand, Category, Product


class UniqueNameSerializer(serializers.ModelSerializer):
    entity_label = ""

    name = serializers.CharField(max_length=100)

    class Meta:
        fields = ["id", "name", "description"]

    def validate_name(self, value):
        duplicates = self.Meta.model.objects.filter(name__iexact=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ConflictError(
                f"{self.entity_label} з назвою «{value}» вже існує. Оберіть іншу назву."
            )
        return value


class CategorySerializer(UniqueNameSerializer):
    entity_label = "Категорія"

    class Meta(UniqueNameSerializer.Meta):
        model = Category


class BrandSerializer(UniqueNameSerializer):
    entity_label = "Бренд"

    class Meta(UniqueNameSerializer.Meta):
        model = Brand


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        error_messages={
            "does_not_exist": "Категорію з id={pk_value} не знайдено.",
            "incorrect_type": "Некоректне значення: потрібне ціле число.",
        },
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        source="brand",
        queryset=Brand.objects.all(),
        error_messages={
            "does_not_exist": "Бренд з id={pk_value} не знайдено.",
            "incorrect_type": "Некоректне значення: потрібне ціле число.",
        },
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    price_per_day = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
        coerce_to_string=False,
        error_messages={
            "min_value": "Ціна за добу має бути більшою за 0.",
        },
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price_per_day",
            "is_available",
            "category_id",
            "category_name",
            "brand_id",
            "brand_name",
        ]

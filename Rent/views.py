from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import ConflictError
from .models import Brand, Category, Product
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductSerializer,
)
from .utils import products_count_text

SORT_FIELDS = (
    "id",
    "-id",
    "name",
    "-name",
    "price_per_day",
    "-price_per_day",
)


def get_or_404(queryset, pk, label):
    try:
        return queryset.get(pk=pk)
    except ObjectDoesNotExist:
        raise NotFound(f"{label} з id={pk} не знайдено.") from None


class ListCreateView(APIView):
    model = None
    serializer_class = None

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetailView(APIView):
    model = None
    serializer_class = None
    label = ""

    def get_queryset(self):
        return self.model.objects.all()

    def get_instance(self, pk):
        return get_or_404(self.get_queryset(), pk, self.label)

    def check_can_delete(self, instance):
        pass

    def get(self, request, pk):
        serializer = self.serializer_class(self.get_instance(pk))
        return Response(serializer.data)

    def update(self, request, pk, partial):
        instance = self.get_instance(pk)
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        return self.update(request, pk, partial=False)

    def patch(self, request, pk):
        return self.update(request, pk, partial=True)

    def delete(self, request, pk):
        instance = self.get_instance(pk)
        self.check_can_delete(instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RelatedProductsView(APIView):
    parent_model = None
    label = ""

    def get(self, request, pk):
        parent = get_or_404(self.parent_model.objects.all(), pk, self.label)
        products = parent.products.select_related("category", "brand")
        return Response(ProductSerializer(products, many=True).data)


def parse_int_param(params, name):
    raw = params.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError({name: ["Значення має бути цілим числом."]}) from None


def parse_bool_param(params, name):
    raw = params.get(name)
    if raw is None or raw == "":
        return None
    value = raw.lower()
    if value in ("true", "1"):
        return True
    if value in ("false", "0"):
        return False
    raise ValidationError({name: ["Допустимі значення: true або false."]})


class ProductListView(ListCreateView):
    model = Product
    serializer_class = ProductSerializer

    def get_queryset(self):
        params = self.request.query_params
        queryset = Product.objects.select_related("category", "brand")

        search = params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        category_id = parse_int_param(params, "category_id")
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)

        brand_id = parse_int_param(params, "brand_id")
        if brand_id is not None:
            queryset = queryset.filter(brand_id=brand_id)

        is_available = parse_bool_param(params, "is_available")
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available)

        sort_by = params.get("sort_by")
        if sort_by:
            if sort_by not in SORT_FIELDS:
                allowed = ", ".join(SORT_FIELDS)
                raise ValidationError({"sort_by": [f"Допустимі значення: {allowed}."]})
            queryset = queryset.order_by(sort_by, "id")
        return queryset


class ProductDetailView(DetailView):
    model = Product
    serializer_class = ProductSerializer
    label = "Товар"

    def get_queryset(self):
        return Product.objects.select_related("category", "brand")


class CategoryListView(ListCreateView):
    model = Category
    serializer_class = CategorySerializer


class CategoryDetailView(DetailView):
    model = Category
    serializer_class = CategorySerializer
    label = "Категорія"

    def check_can_delete(self, instance):
        count = instance.products.count()
        if count:
            raise ConflictError(
                f"Неможливо видалити категорію «{instance.name}», оскільки "
                f"за нею закріплено {products_count_text(count)}. "
                "Спершу видаліть ці товари або перенесіть їх в іншу "
                "категорію."
            )


class CategoryProductsView(RelatedProductsView):
    parent_model = Category
    label = "Категорія"


class BrandListView(ListCreateView):
    model = Brand
    serializer_class = BrandSerializer


class BrandDetailView(DetailView):
    model = Brand
    serializer_class = BrandSerializer
    label = "Бренд"

    def check_can_delete(self, instance):
        count = instance.products.count()
        if count:
            raise ConflictError(
                f"Неможливо видалити бренд «{instance.name}», оскільки "
                f"за ним закріплено {products_count_text(count)}. "
                "Спершу видаліть ці товари або перенесіть їх до іншого "
                "бренду."
            )


class BrandProductsView(RelatedProductsView):
    parent_model = Brand
    label = "Бренд"


class ApiNotFoundView(APIView):
    def initial(self, request, *args, **kwargs):
        raise NotFound(
            f"Ендпоінт {request.method} {request.path} не існує. "
            "Перевірте адресу (URL записуються без завершального «/»)."
        )

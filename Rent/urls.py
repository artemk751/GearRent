from django.urls import path, re_path

from . import views

urlpatterns = [
    path("products", views.ProductListView.as_view(), name="product-list"),
    path(
        "products/<int:pk>",
        views.ProductDetailView.as_view(),
        name="product-detail",
    ),
    path("categories", views.CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<int:pk>",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path(
        "categories/<int:pk>/products",
        views.CategoryProductsView.as_view(),
        name="category-products",
    ),
    path("brands", views.BrandListView.as_view(), name="brand-list"),
    path(
        "brands/<int:pk>",
        views.BrandDetailView.as_view(),
        name="brand-detail",
    ),
    path(
        "brands/<int:pk>/products",
        views.BrandProductsView.as_view(),
        name="brand-products",
    ),
    re_path(r"^.*$", views.ApiNotFoundView.as_view(), name="api-not-found"),
]

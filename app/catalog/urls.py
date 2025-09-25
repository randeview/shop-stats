from django.urls import path

from .views import (
    CategoryTreeView,
    ProductAggregatedExportXLSXView,
    ProductAggregatedListView,
)

app_name = "catalog"

urlpatterns = [
    path("categories/", CategoryTreeView.as_view(), name="categories-tree"),
    path("products/", ProductAggregatedListView.as_view(), name="products-aggregated"),
    path(
        "products.xlsx/",
        ProductAggregatedExportXLSXView.as_view(),
        name="products-aggregated-export",
    ),
]

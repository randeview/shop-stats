from django.urls import path

from .views import CategoryTreeView, ProductListView

app_name = "catalog"

urlpatterns = [
    path("categories/", CategoryTreeView.as_view(), name="categories-tree"),
    path("products/", ProductListView.as_view(), name="products"),
]

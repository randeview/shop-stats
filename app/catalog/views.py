from django_filters.rest_framework import FilterSet, NumberFilter
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from app.catalog.models import Category, Product
from app.catalog.serializers import CategoryTreeSerializer, ProductSerializer


class HundredPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 1000  # optional if you allow client override with ?page_size=


@extend_schema(
    tags=["catalog"],
    summary="List category tree",
    description="Returns hierarchical category tree up to 3 levels",
    responses=CategoryTreeSerializer(many=True),
)
class CategoryTreeView(generics.ListAPIView):
    # permission_classes = [permissions.IsAuthenticated, DeviceBound, HasPaidService]
    permission_classes = [permissions.AllowAny]
    serializer_class = CategoryTreeSerializer

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True).prefetch_related(
            "children__children"
        )


class ProductFilter(FilterSet):
    category_id = NumberFilter(field_name="category_id", lookup_expr="exact")

    class Meta:
        model = Product
        fields = [
            "category_id",
        ]


@extend_schema(
    tags=["catalog"],
    summary="List products",
    description="Flat list of products with filters; use ordering for sort.",
    responses=ProductSerializer(many=True),
)
class ProductListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    pagination_class = HundredPagination
    # permission_classes = [permissions.IsAuthenticated, DeviceBound, HasPaidService]
    serializer_class = ProductSerializer
    # filter_backends = [
    #     DjangoFilterBackend,
    #     filters.SearchFilter,
    #     filters.OrderingFilter,
    # ]
    filterset_class = ProductFilter
    search_fields = ["name", "category__name"]
    ordering_fields = [
        "created_at",
    ]
    ordering = ["id"]

    def get_queryset(self):
        # Keep it efficient
        qs = Product.objects.select_related("category").all()
        return qs

    def list(self, request, *args, **kwargs):
        rows = Product.objects.values(
            "photo_url",
            "name",
            "category__name",
            "article_id",
            "merchant_name",
            "product_count",
            "product_orders",
            "gmv",
        )

        agg = {}
        for r in rows:
            key = r["article_id"]
            if key not in agg:
                agg[key] = {
                    "photo_url": r["photo_url"],
                    "name": r["name"],
                    "category_name": r["category__name"],
                    "article_id": key,
                    "merchant_names": set(),
                    "product_count": 0,
                    "product_orders": 0,
                    "gmv_sum": 0,
                }
            g = agg[key]
            g["merchant_names"].add(r["merchant_name"])
            g["product_count"] += r["product_count"] or 0
            g["product_orders"] += r["product_orders"] or 0
            g["gmv_sum"] += r["gmv"] or 0

        # finalize
        data = []
        for g in agg.values():
            names = sorted(g["merchant_names"])
            product_count = g["product_count"]
            data.append(
                {
                    "photo_url": g["photo_url"],
                    "name": g["name"],
                    "category_name": g["category_name"],
                    "article_id": g["article_id"],
                    "merchant_count": len(names),
                    "merchant_names": names,
                    "product_count": product_count,
                    "product_orders": g["product_orders"],
                    "gmv_sum": g["gmv_sum"],
                    "gmv_each": (g["gmv_sum"] / product_count) if product_count else 0,
                }
            )

        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)

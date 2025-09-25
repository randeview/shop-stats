from django_filters.rest_framework import FilterSet, NumberFilter
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from app.catalog.models import Category, Product
from app.catalog.serializers import AggregatedProductSerializer, CategoryTreeSerializer


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
    pagination_class = None

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
    parameters=[
        OpenApiParameter(
            "search",
            OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Search by name/category name",
        ),
        OpenApiParameter("category_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter(
            "min_merchant_count", OpenApiTypes.INT, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "max_merchant_count", OpenApiTypes.INT, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "min_product_orders", OpenApiTypes.INT, OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            "max_product_orders", OpenApiTypes.INT, OpenApiParameter.QUERY
        ),
        OpenApiParameter("min_gmv_sum", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("max_gmv_sum", OpenApiTypes.INT, OpenApiParameter.QUERY),
    ],
    responses=AggregatedProductSerializer(many=True),
)
class ProductListView(generics.ListAPIView):
    # permission_classes = [permissions.IsAuthenticated, DeviceBound, HasPaidService]
    permission_classes = [permissions.AllowAny]
    pagination_class = HundredPagination
    serializer_class = AggregatedProductSerializer

    def get_queryset(self):
        qs = Product.objects.select_related("category").all()
        return qs

    def list(self, request, *args, **kwargs):
        qs = Product.objects.values(
            "photo_url",
            "name",
            "category",
            "category__name",
            "article_id",
            "merchant_name",
            "product_count",
            "product_orders",
            "gmv",
        )
        # --- Filtering by category ---
        category_id = request.query_params.get("category_id")
        if category_id:
            qs = qs.filter(category_id=category_id)

        agg = {}
        for r in qs:
            key = r["article_id"]
            if key not in agg:
                agg[key] = {
                    "photo_url": r["photo_url"],
                    "name": r["name"],
                    "category": r["category"],
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
                    "photo_url": (
                        g["photo_url"]
                        if g["photo_url"]
                        else "https://resources.cdn-kaspi.kz/img/m/p/h98/h2c/84198210273310.jpg?format=preview-large"
                    ),
                    "name": g["name"],
                    "category": g["category"],
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
        # --- Merchant count filters ---
        min_count = request.query_params.get("min_merchant_count")
        max_count = request.query_params.get("max_merchant_count")
        if min_count is not None:
            data = [d for d in data if d["merchant_count"] >= int(min_count)]
        if max_count is not None:
            data = [d for d in data if d["merchant_count"] <= int(max_count)]

        # --- Product orders filters ---
        min_orders = request.query_params.get("min_product_orders")
        max_orders = request.query_params.get("max_product_orders")
        if min_orders is not None:
            data = [d for d in data if d["product_orders"] >= int(min_orders)]
        if max_orders is not None:
            data = [d for d in data if d["product_orders"] <= int(max_orders)]

        # --- Product orders filters ---
        min_gmv = request.query_params.get("min_gmv_sum")
        max_gmv = request.query_params.get("max_gmv_sum")
        if min_gmv is not None:
            data = [d for d in data if d["gmv_sum"] >= int(min_gmv)]
        if max_gmv is not None:
            data = [d for d in data if d["gmv_sum"] <= int(max_gmv)]
        # --- Search filter ---
        search = request.query_params.get("search")
        if search:
            search_lower = search.lower()
            data = [
                d
                for d in data
                if search_lower in (d["name"] or "").lower()
                or search_lower in (d["category_name"] or "").lower()
            ]
        # --- Pagination ---
        page = self.paginate_queryset(data)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)

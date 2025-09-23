from django_filters.rest_framework import (
    CharFilter,
    DjangoFilterBackend,
    FilterSet,
    NumberFilter,
)
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import filters, generics, permissions

from app.catalog.models import Category, Product
from app.catalog.serializers import CategoryTreeSerializer, ProductSerializer


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
    category_slug = CharFilter(method="filter_category_slug")
    min_price = NumberFilter(field_name="price", lookup_expr="gte")
    max_price = NumberFilter(field_name="price", lookup_expr="lte")
    min_rating = NumberFilter(field_name="rating", lookup_expr="gte")
    max_rating = NumberFilter(field_name="rating", lookup_expr="lte")

    def filter_category_slug(self, queryset, name, value):
        return queryset.filter(category__slug=value)

    class Meta:
        model = Product
        fields = ["category_id", "min_price", "max_price", "min_rating", "max_rating"]


@extend_schema(
    tags=["catalog"],
    summary="List products",
    description="Flat list of products with filters; use ordering for sort.",
    parameters=[
        OpenApiParameter(
            "search",
            OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Search by name/slug/category name",
        ),
        OpenApiParameter(
            "ordering",
            OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Sort by: absolute_position, price, sales_30d, rating, created_at (prefix with '-' for desc)",
        ),
        OpenApiParameter("category_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        OpenApiParameter("category_slug", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("min_price", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("max_price", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("min_rating", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
        OpenApiParameter("max_rating", OpenApiTypes.NUMBER, OpenApiParameter.QUERY),
    ],
    responses=ProductSerializer(many=True),
)
class ProductListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    # permission_classes = [permissions.IsAuthenticated, DeviceBound, HasPaidService]
    serializer_class = ProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
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

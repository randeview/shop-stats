from django_filters.rest_framework import (
    CharFilter,
    DjangoFilterBackend,
    FilterSet,
    NumberFilter,
)
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import filters, generics, permissions, serializers
from rest_framework.permissions import AllowAny

from .models import Category, Product


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "level", "children")

    def get_children(self, obj):
        if obj.children.exists():
            return CategoryTreeSerializer(obj.children.all(), many=True).data
        return []


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "photo_url",
            "category",
            "category_name",
            "absolute_position",
            "price",
            "sellers_count",
            "sales_30d",
            "reviews_count",
            "rating",
            "weight_kg",
            "created_at",
        )


@extend_schema(
    tags=["catalog"],
    summary="List category tree",
    description="Returns hierarchical category tree up to 3 levels",
    responses=CategoryTreeSerializer(many=True),
)
class CategoryTreeView(generics.ListAPIView):
    permission_classes = [AllowAny]
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
    serializer_class = ProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "slug", "category__name"]
    ordering_fields = [
        "absolute_position",
        "price",
        "sales_30d",
        "rating",
        "created_at",
    ]
    ordering = ["absolute_position", "id"]

    def get_queryset(self):
        # Keep it efficient
        qs = Product.objects.select_related("category").all()
        return qs

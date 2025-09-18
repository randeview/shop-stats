from rest_framework import serializers

from app.catalog.models import Category, Product


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

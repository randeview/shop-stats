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
    absolut_position = serializers.IntegerField(default=1, read_only=True)

    class Meta:
        model = Product
        fields = (
            "photo_url",
            "name",
            "category_name",
            "absolut_position",
            "article_id",
            "merchant_name",
            "product_count",
            "product_orders",
            "gmv",
        )

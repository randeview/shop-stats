from rest_framework import serializers

from app.catalog.models import Category


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "level", "children")

    def get_children(self, obj):
        if obj.children.exists():
            return CategoryTreeSerializer(obj.children.all(), many=True).data
        return []


class AggregatedProductSerializer(serializers.Serializer):
    article_id = serializers.CharField()
    photo_url = serializers.CharField(allow_null=True)
    name = serializers.CharField()
    category = serializers.IntegerField()
    category_name = serializers.CharField()
    absolut_position = serializers.IntegerField(default=1)
    merchant_count = serializers.IntegerField()
    merchant_names = serializers.ListField(child=serializers.CharField())
    product_count = serializers.IntegerField()
    product_orders = serializers.IntegerField()
    gmv_sum = serializers.IntegerField()
    gmv_each = serializers.FloatField()

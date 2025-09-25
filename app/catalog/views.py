from datetime import datetime
from io import BytesIO

from django.http import HttpResponse
from django_filters.rest_framework import FilterSet, NumberFilter
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from openpyxl import Workbook
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from app.catalog.models import Category, Product
from app.catalog.serializers import AggregatedProductSerializer, CategoryTreeSerializer
from app.catalog.services import aggregate_products


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
class ProductAggregatedListView(generics.ListAPIView):
    # permission_classes = [permissions.IsAuthenticated, DeviceBound, HasPaidService]
    permission_classes = [permissions.AllowAny]
    pagination_class = HundredPagination
    serializer_class = AggregatedProductSerializer

    def get_queryset(self):
        qs = Product.objects.select_related("category").all()
        return qs

    def list(self, request, *args, **kwargs):
        data = aggregate_products(request)
        page = self.paginate_queryset(data)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["catalog"],
    summary="Aggregated products (XLSX export)",
    responses={200: OpenApiResponse(description="XLSX file download")},
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
)
class ProductAggregatedExportXLSXView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        data = aggregate_products(request)

        wb = Workbook()
        ws = wb.active
        ws.title = "Products"

        headers = [
            "photo_url",
            "name",
            "category_name",
            "article_id",
            "merchant_count",
            "merchant_names",
            "product_count",
            "product_orders",
            "gmv_sum",
            "gmv_each",
        ]
        ws.append(headers)

        for row in data:
            ws.append(
                [
                    row["photo_url"],
                    row["name"],
                    row["category_name"],
                    row["article_id"],
                    row["merchant_count"],
                    ", ".join(row["merchant_names"]),
                    row["product_count"],
                    row["product_orders"],
                    row["gmv_sum"],
                    float(f'{row["gmv_each"]:.4f}'),
                ]
            )

        buf = BytesIO()
        wb.save(buf)
        wb.close()
        buf.seek(0)

        filename = (
            f'products_aggregated_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        resp = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

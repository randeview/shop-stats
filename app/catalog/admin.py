from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .importer import import_categories_from_xlsx
from .models import Category, Product


class CategoryImportForm(forms.Form):
    file = forms.FileField(label="XLSX файл")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "level")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    def level(self, obj):
        return obj.level

    level.short_description = _("level")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "merchant_name",
        "article_id",
    )
    list_filter = ("category",)
    search_fields = ("name",)
    autocomplete_fields = ("category",)
    change_list_template = "admin/product_list_change.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-xlsx/",
                self.admin_site.admin_view(self.import_xlsx_view),
                name="catalog_category_product_import",
            ),
        ]
        return custom + urls

    def import_xlsx_view(self, request):
        if not self.has_change_permission(request):
            self.message_user(request, _("No permission"), level=messages.ERROR)
            return redirect("admin:catalog_product_changelist")

        if request.method == "POST":
            form = CategoryImportForm(request.POST, request.FILES)
            if form.is_valid():
                created = import_categories_from_xlsx(
                    file_obj=form.cleaned_data["file"],
                    sheet_name=form.cleaned_data.get("sheet_name") or None,
                )
                self.message_user(
                    request,
                    _(
                        "Import queued/finished. Created approximately %(count)d categories."
                    )
                    % {"count": created},
                    level=messages.SUCCESS,
                )
                return redirect("admin:catalog_product_changelist")

        else:
            form = CategoryImportForm()

        context = dict(
            self.admin_site.each_context(request),
            title=_("Import categories from XLSX"),
            form=form,
        )
        return render(request, "admin/import_xlsx.html", context)

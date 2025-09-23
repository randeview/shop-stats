from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


def validate_max_depth(parent):
    """
    Enforces category depth <= 3 (levels: 1, 2, 3).
    """
    depth = 1
    node = parent
    while node:
        depth += 1
        node = node.parent
        if depth > 3:
            raise ValidationError(_("Category depth cannot exceed 3 levels."))


class Category(models.Model):
    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        unique_together = (("parent", "slug"),)
        indexes = [
            models.Index(fields=["parent", "slug"]),
            models.Index(fields=["name"]),
        ]
        ordering = ["parent__id", "name"]

    def clean(self):
        # Prevent cycles and enforce depth
        seen = set()
        p = self.parent
        while p:
            if p.pk == self.pk:
                raise ValidationError(_("Category cannot be its own ancestor."))
            if p.pk in seen:
                raise ValidationError(_("Circular parent relationship detected."))
            seen.add(p.pk)
            p = p.parent
        if self.parent:
            validate_max_depth(self.parent)

    @property
    def level(self) -> int:
        """1..3"""
        lvl, p = 1, self.parent
        while p:
            lvl += 1
            p = p.parent
        return lvl

    def __str__(self):
        parts = [self.name]
        p = self.parent
        while p:
            parts.append(p.name)
            p = p.parent
        return " / ".join(reversed(parts))


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name=_("category"),
        on_delete=models.PROTECT,
        related_name="products",
    )
    merchant_name = models.CharField(
        _("merchant name"), max_length=512, blank=True, null=True
    )
    name = models.CharField(_("name"), max_length=255)
    photo_url = models.URLField(_("photo URL"), max_length=1000, blank=True, null=True)
    article_id = models.CharField(
        _("article ID"), max_length=255, blank=True, null=True
    )
    product_count = models.PositiveIntegerField(_("count"), default=0)
    product_orders = models.PositiveIntegerField(_("product orders"), default=0)

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ["id"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["article_id"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

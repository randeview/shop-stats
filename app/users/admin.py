# users/admin.py
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.shortcuts import get_object_or_404, redirect
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    change_form_template = "admin/user_change.html"  # your custom template

    # Add our fields to the default fieldsets of BaseUserAdmin
    fieldsets = BaseUserAdmin.fieldsets + (
        (_("Статус оплаты"), {"fields": ("payment_status",)}),
        (_("Устройство"), {"fields": ("device_id",)}),
    )

    # List page
    list_display = (
        "username",
        "phone_number",
        "payment_status",
        "device_id",
        "is_active",
    )
    list_filter = ("payment_status", "is_active", "is_staff")

    # Bulk actions
    actions = ["mark_as_paid", "mark_as_not_paid", "reset_device_binding"]

    @admin.action(description=_("Mark selected users as PAID"))
    def mark_as_paid(self, request, queryset):
        updated = queryset.exclude(payment_status=User.PaymentStatus.PAID).update(
            payment_status=User.PaymentStatus.PAID
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d user marked as PAID",
                "%(count)d users marked as PAID",
                updated,
            )
            % {"count": updated},
            level=messages.SUCCESS,
        )

    @admin.action(description=_("Mark selected users as NOT PAID"))
    def mark_as_not_paid(self, request, queryset):
        updated = queryset.exclude(payment_status=User.PaymentStatus.NOT_PAID).update(
            payment_status=User.PaymentStatus.NOT_PAID
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d user marked as NOT PAID",
                "%(count)d users marked as NOT PAID",
                updated,
            )
            % {"count": updated},
            level=messages.SUCCESS,
        )

    @admin.action(description=_("Reset device (allow re-login on new device)"))
    def reset_device_binding(self, request, queryset):
        updated = 0
        # Need per-row to bump token_version
        for u in queryset.only("id", "device_id", "token_version"):
            if u.device_id:
                u.device_id = None
                u.save(update_fields=["device_id"])
            u.bump_token_version()
            updated += 1
        self.message_user(
            request,
            ngettext(
                "%(count)d user device reset",
                "%(count)d users device reset",
                updated,
            )
            % {"count": updated},
            level=messages.SUCCESS,
        )

    # Object-tools buttons on the change page
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/reset-device/",
                self.admin_site.admin_view(self.reset_device_view),
                name="users_user_reset_device",
            ),
            path(
                "<path:object_id>/mark-paid/",
                self.admin_site.admin_view(self.mark_paid_view),
                name="users_user_mark_paid",
            ),
        ]
        return custom + urls

    def _ensure_change_perm(self, request, object_id):
        if not self.has_change_permission(request):
            self.message_user(request, _("No permission"), level=messages.ERROR)
            return redirect("admin:users_user_change", object_id)

    def reset_device_view(self, request, object_id):
        maybe_redirect = self._ensure_change_perm(request, object_id)
        if maybe_redirect:
            return maybe_redirect
        user = get_object_or_404(User, pk=object_id)
        if user.device_id:
            user.device_id = None
            user.save(update_fields=["device_id"])
        user.bump_token_version()
        self.message_user(request, _("Device reset"), level=messages.SUCCESS)
        return redirect("admin:users_user_change", object_id)

    def mark_paid_view(self, request, object_id):
        maybe_redirect = self._ensure_change_perm(request, object_id)
        if maybe_redirect:
            return maybe_redirect
        user = get_object_or_404(User, pk=object_id)
        if user.payment_status != User.PaymentStatus.PAID:
            user.payment_status = User.PaymentStatus.PAID
            user.save(update_fields=["payment_status"])
        self.message_user(request, _("User marked as PAID"), level=messages.SUCCESS)
        return redirect("admin:users_user_change", object_id)

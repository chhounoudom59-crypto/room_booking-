from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom form for creating users without a username field."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    """Custom form for changing users without a username field."""

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


class CustomUserAdmin(UserAdmin):
    model = User
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = (
        "email",
        "student_id",
        "faculty",
        "department",
        "booking_approval_status",
        "is_superuser",
        "is_active",
    )
    list_filter = ("is_superuser", "is_active", "booking_approval_status", "faculty")

    # Disable bulk actions
    actions = []

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "student_id",
                    "phone_number",
                    "faculty",
                    "department",
                    "profile_picture",
                )
            },
        ),
        ("Booking Verification", {"fields": ("booking_approval_status",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "student_id",
                    "phone_number",
                    "faculty",
                    "department",
                    "booking_approval_status",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # Only use fields that exist on the custom User model (no 'username')
    search_fields = ("email", "student_id", "first_name", "last_name", "faculty", "department")

    # Order by email — there is no username field
    ordering = ("email",)

    # Auto-managed fields are read-only
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")


admin.site.register(User, CustomUserAdmin)

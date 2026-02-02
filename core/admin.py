# /Users/ijaehwa/github/dev_cj/dev_cj_v2/core/admin.py
from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


class UserAdminForm(forms.ModelForm):
    """
    관리자 화면에서 login_id는 직접 입력하지 않고,
    affiliation + employee_no로 자동 생성합니다.
    """
    class Meta:
        model = User
        fields = ("affiliation", "employee_no", "full_name", "email", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.affiliation and instance.employee_no:
            instance.login_id = f"{instance.affiliation}:{instance.employee_no.strip()}"
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    form = UserAdminForm

    ordering = ("login_id",)
    list_display = ("login_id", "affiliation", "employee_no", "full_name", "is_staff", "is_superuser", "is_active")
    search_fields = ("login_id", "employee_no", "full_name")
    list_filter = ("affiliation", "is_staff", "is_superuser", "is_active")

    readonly_fields = ("login_id", "last_login", "date_joined")

    fieldsets = (
        ("기본 정보", {"fields": ("login_id", "affiliation", "employee_no", "full_name", "email", "password")}),
        ("권한", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("기타", {"fields": ("last_login", "date_joined")}),
    )

    # add(생성) 화면에서는 DjangoUserAdmin 기본 add_form이 USERNAME_FIELD를 요구합니다.
    # 다만 우리는 login_id를 자동 생성하고 싶으므로 add_form을 커스텀하는 게 정석입니다.
    # 우선은 생성은 쉘/관리 커맨드로 하고, admin에서는 수정 중심으로 운영하셔도 됩니다.

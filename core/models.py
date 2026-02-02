from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, login_id, password=None, **extra_fields):
        if not login_id:
            raise ValueError("login_id 는 필수입니다.")

        user = self.model(login_id=login_id, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(login_id=login_id, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(
        "email address",
        blank=True,
        null=True,
        db_index=True,
    )

    AFFILIATION_CHOICES = (
        ("HQ", "지주사"),
        ("OV", "올리브영"),
        ("DT", "대한통운"),
        ("JJ", "제일제당"),
        ("ENM", "ENM"),
        ("FD", "푸드빌"),
    )


    login_id = models.CharField(max_length=120, unique=True)
    affiliation = models.CharField(max_length=20, choices=AFFILIATION_CHOICES)
    full_name = models.CharField(max_length=50)
    employee_no = models.CharField(max_length=30, db_index=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    
    USERNAME_FIELD = "login_id"
    REQUIRED_FIELDS = []


    def get_display_identity(self) -> str:
        """
        상단 헤더 등에 표시할 사용자 식별 문자열을 반환합니다.

        Returns:
            str:
            1) email이 있으면 email
            2) email이 없으면 "사번:이름"
            3) 그마저도 없으면 login_id
        """
        if self.email:
            return self.email

        if self.employee_no and self.full_name:
            return f"{self.employee_no}:{self.full_name}"

        return self.login_id


    def save(self, *args, **kwargs):
        """
        affiliation + employee_no 기반으로 login_id를 자동 동기화합니다.
        """
        if self.affiliation and self.employee_no:
            self.login_id = f"{self.affiliation}:{self.employee_no.strip()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.affiliation}:{self.full_name}"
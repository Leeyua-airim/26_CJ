# /Users/ijaehwa/github/dev_cj/dev_cj_v2/core/forms.py
from django import forms
from .models import User
from allauth.account.forms import LoginForm
from django.utils.translation import gettext_lazy as _


class LocalCompositeLoginForm(LoginForm):
    """
    소속 + 사번 + 비밀번호로 로컬 로그인을 수행하는 폼
    - 내부 인증 키(login)는 "HQ:CJ000001" 형태로 주입합니다.
    """

    affiliation = forms.ChoiceField(
        choices=(
            ("HQ", "지주사"),
            ("OV", "올리브영"),
            ("DT", "대한통운"),
            ("JJ", "제일제당"),
            ("ENM", "ENM"),
            ("FD", "푸드빌"),
        ),
        required=True,
        label=_("소속"),
    )

    employee_no = forms.CharField(
        max_length=30,
        required=True,
        label=_("사번"),
    )

    # allauth가 내부적으로 사용하는 필드명들
    # (버전/설정에 따라 login/username 경로가 달라서 둘 다 준비합니다)
    login = forms.CharField(required=False)
    username = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        """
        중요한 포인트:
        - required 검증은 clean()보다 먼저 일어납니다.
        - 그래서 clean()에서 login을 주입하면 늦습니다.
        - __init__에서 self.data(QueryDict)에 login을 미리 넣어야 합니다.
        """
        super().__init__(*args, **kwargs)

        if self.is_bound:
            data = self.data.copy()

            affiliation = (data.get("affiliation") or "").strip()
            employee_no = (data.get("employee_no") or "").strip()

            if affiliation and employee_no:
                composite_login_id = f"{affiliation}:{employee_no}"

                # ✅ 필드 검증 전에 주입
                data["login"] = composite_login_id
                data["username"] = composite_login_id

            self.data = data

    def clean(self):
        """
        allauth 기본 검증/인증 흐름을 그대로 사용합니다.
        """
        cleaned_data = super().clean()
        return cleaned_data



class ProfileCompleteForm(forms.ModelForm):
    """
    소셜 로그인 최초 가입 사용자의 필수 프로필을 완성하기 위한 폼입니다.
    """

    class Meta:
        model = User
        fields = ["affiliation", "employee_no", "full_name"]

    def clean_employee_no(self):
        """
        Returns:
            str: 공백 제거된 사번 문자열
        """
        employee_no = self.cleaned_data.get("employee_no", "")

        if employee_no is None:
            raise forms.ValidationError("사번은 필수입니다.")

        employee_no = employee_no.strip()

        if not employee_no:
            raise forms.ValidationError("사번은 필수입니다.")

        return employee_no

    def clean_full_name(self):
        """
        Returns:
            str: 공백 제거된 이름 문자열
        """
        full_name = self.cleaned_data.get("full_name", "")

        if full_name is None:
            raise forms.ValidationError("성명은 필수입니다.")

        full_name = full_name.strip()

        if not full_name:
            raise forms.ValidationError("성명은 필수입니다.")

        return full_name

    def clean_affiliation(self):
        """
        Returns:
            str: 선택된 affiliation 코드
        """
        affiliation = self.cleaned_data.get("affiliation")

        if not affiliation:
            raise forms.ValidationError("소속은 필수입니다.")

        return affiliation

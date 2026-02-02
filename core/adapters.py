"""
core/adapters.py

- 일반 사용자는 Google SSO로만 가입/로그인 유도
- 로컬 회원가입은 기업회원(초대 토큰 보유자)에게만 허용
- Google SSO 가입은 특정 도메인만 허용(선택)
"""
import os
from __future__ import annotations

from typing import Optional

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.core.exceptions import PermissionDenied


def _get_email_domain(email: str) -> str:
    """
    이메일 주소에서 도메인만 추출합니다.

    Parameters:
        email: 예) "user@example.com"

    Returns:
        "example.com"
    """
    email = (email or "").strip().lower()
    if "@" not in email:
        return ""
    return email.split("@", 1)[1]


class DomainRestrictedAccountAdapter(DefaultAccountAdapter):
    """
    로컬(account) 회원가입 제한 어댑터

    정책:
    - 기본적으로 로컬 회원가입은 닫습니다.
    - 단, ?invite=... 가 맞는 경우에만 회원가입을 엽니다.
    """

    def is_open_for_signup(self, request) -> bool:
        """
        로컬 회원가입 가능 여부를 결정합니다.

        - request가 없으면 False
        - invite 토큰이 환경변수 ENTERPRISE_SIGNUP_TOKEN과 일치할 때만 True
        """
        if request is None:
            return False

        # 로컬 signup은 초대 토큰이 있어야 허용
        invite_token = (request.GET.get("invite") or "").strip()
        expected = (os.getenv("ENTERPRISE_SIGNUP_TOKEN", "") or "").strip()

        if expected and invite_token == expected:
            return True

        return False


class DomainRestrictedSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    소셜(socialaccount) 가입 제한 어댑터

    정책(선택):
    - ALLOWED_SIGNUP_DOMAINS가 비어 있으면: 모두 허용 (개발 단계)
    - 값이 있으면: 해당 도메인만 허용
    """

    def pre_social_login(self, request, sociallogin) -> None:
        """
        소셜 로그인 콜백 단계에서 가입/로그인을 사전 검사합니다.

        도메인 제한을 적용할 경우:
        - 이메일 도메인이 허용 목록에 없으면 차단합니다.
        """
        email: Optional[str] = None

        user = getattr(sociallogin, "user", None)
        if user is not None:
            email = getattr(user, "email", None)

        email = (email or "").strip().lower()
        domain = _get_email_domain(email)

        allowed = getattr(settings, "ALLOWED_SIGNUP_DOMAINS", []) or []
        allowed = [d.strip().lower() for d in allowed if d.strip()]

        # allowed가 비어있으면 개발 단계에서 전체 허용
        if not allowed:
            return

        if domain not in allowed:
            raise PermissionDenied("허용되지 않은 이메일 도메인입니다.")

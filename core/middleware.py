from django.shortcuts import redirect
from django.urls import reverse

class ProfileCompletionMiddleware:
    """
    프로필이 완성되지 않은 사용자가 /app/ 이하 기능을 사용하지 못하도록 강제합니다.

    규칙:
        - 로그인된 사용자가
        - affiliation/employee_no/full_name 중 하나라도 비어 있으면
        - /app/profile/complete/ 로 이동시킵니다.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path

            profile_url = reverse("profile_complete")

            # 프로필 입력 페이지/로그아웃/관리자/정적 리소스 등은 제외합니다.
            allow_prefixes = [
                profile_url,
                "/accounts/",
                "/admin/",
                "/static/",
                "/media/",
            ]

            is_allowed = False
            for prefix in allow_prefixes:
                if path.startswith(prefix):
                    is_allowed = True

            if not is_allowed:
                user = request.user
                if (not user.affiliation) or (not user.employee_no) or (not user.full_name):
                    return redirect(profile_url)

        response = self.get_response(request)
        return response

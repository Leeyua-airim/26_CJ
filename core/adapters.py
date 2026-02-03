import uuid
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Google SSO 자동 가입 시, 커스텀 User 모델의 USERNAME_FIELD(login_id)가 비어 있으면 저장이 실패합니다.

    해결:
        - social signup 시점에 임시 login_id(UUID 기반)를 채워서 저장되도록 보장합니다.
        - affiliation/employee_no는 이후 프로필 완성 화면에서 받습니다.
    """

    def populate_user(self, request, sociallogin, data):
        """
        allauth가 소셜 로그인 사용자 객체를 구성할 때 호출합니다.

        Parameters:
            request: HttpRequest
            sociallogin: SocialLogin
            data: dict (provider가 제공하는 사용자 정보)

        Returns:
            User: populate 된 사용자 객체
        """
        user = super().populate_user(request, sociallogin, data)

        if not getattr(user, "login_id", None):
            temp_id = uuid.uuid4().hex
            user.login_id = f"social:{temp_id}"

        # Google 프로필에 name이 있으면 임시로 full_name에 채웁니다(최종 입력은 사용자가 확정).
        name = data.get("name")
        if name and not getattr(user, "full_name", ""):
            user.full_name = name

        return user

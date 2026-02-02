from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/".env")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", 
                       "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

ALLOWED_SIGNUP_DOMAINS = [
    d.strip().lower()
    for d in os.getenv("ALLOWED_SIGNUP_DOMAINS", "").split(",")
    if d.strip()
]

# ACCOUNT_ADAPTER = "core.adapters.DomainRestrictedAccountAdapter"
# SOCIALACCOUNT_ADAPTER = "core.adapters.DomainRestrictedSocialAccountAdapter"


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Add
    "django.contrib.sites",
    # App
    'core', 
    
    # SSO 
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # "allauth.socialaccount.providers.openid_connect",
    "allauth.socialaccount.providers.google",
]

SITE_ID = 1

"""
Authentication / SSO initial setup

- django-allauth 기반 로컬 로그인 + Google SSO 병행
- 초기 컨셉 단계이므로:
  - 소셜 로그인 시 추가 회원정보 입력 없이 자동 가입
  - 로그인 성공 후 /app/ 으로 이동 (빈 화면)
- 추후 서비스 정책 확정 시:
  - 이메일 필수 여부
  - 추가 signup 필드
  - 조직/권한 로직
  등을 확장 예정
"""


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]


LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],

        # (핵심) 소셜에서 verified email을 받았고,
        # 그 이메일이 기존 로컬 계정(User)에 있으면 그 계정으로 로그인 처리
        "EMAIL_AUTHENTICATION": True,

        # (권장) 이후부터는 이메일이 바뀌어도 구글 로그인이 되도록
        # SocialAccount를 기존 로컬 계정에 자동 연결
        "EMAIL_AUTHENTICATION_AUTO_CONNECT": True,
    }
}



# allauth settings 최신 설정으로 정리
# 로그인은 username 기반(로컬), 구글은 별도 버튼
ACCOUNT_LOGIN_METHODS = {"username"}


ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True

# 로컬 가입 시 email까지 받는 형태로 정리
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]

# 아래 2개는 SIGNUP_FIELDS로 대체되는 흐름이라, 가능하면 정리 권장
# (하위 호환을 위해 당장은 둬도 되지만, 중복/혼선을 줄이려면 정리하는 편이 낫습니다)
# ACCOUNT_EMAIL_REQUIRED = True
# SOCIALACCOUNT_EMAIL_REQUIRED = True


# 소셜 로그인 : 추가 가입 화면으로 보내지 말고 자동으로 계정 생성 및 연결
SOCIALACCOUNT_AUTO_SIGNUP = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
        
    # 추가 (allauth 65+ 필수)
    "allauth.account.middleware.AccountMiddleware",

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.debug', # 추가 
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

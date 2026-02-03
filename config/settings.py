from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/".env")

"""키 관리"""
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", 
                       "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
# 만약 키가 없을시 예외 발생
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY가 .env에 설정되어 있지 않습니다.")

# OpenAI Key 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "cj-demo")
PINECONE_HOST = os.getenv("PINECONE_HOST", "")

# Step 5: Embedding 설정(고정)
OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"
OPENAI_EMBEDDING_DIM = 1024

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
SOCIALACCOUNT_ADAPTER = "core.adapters.CustomSocialAccountAdapter"



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
    "gpt_chat",
    
    # Add
    "agent_work",
    "knowledge_base",

    # SSO 
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

SITE_ID = 1

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
    }
}

ACCOUNT_LOGIN_METHODS = {"username"}


ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = False
ACCOUNT_SIGNUP_FIELDS = []
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

    "core.middleware.ProfileCompletionMiddleware",
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
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# config/settings.py
AUTH_USER_MODEL = "core.User"

ACCOUNT_FORMS = {
    "login": "core.forms.LocalCompositeLoginForm",
}


# allauth가 username 필드를 찾을 때, 우리 커스텀 User의 login_id를 사용하도록 지정
ACCOUNT_USER_MODEL_USERNAME_FIELD = "login_id"

# email 필드명도 명시(권장)
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"


# 개발환경에서는 반드시 False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# 30MB 업로드 제한
DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024
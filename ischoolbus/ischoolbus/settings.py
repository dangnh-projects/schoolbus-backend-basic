from .common_settings import *
from datetime import timedelta

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOW_SEND_EMAIL = True
ALLOWED_HOSTS = []
TIME_ZONE = 'Asia/Ho_Chi_Minh'

if ALLOW_SEND_EMAIL:
    EMAIL_HOST = "smtp.office365.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_USERNAME', 'thaitc@nhg.vn')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD ', '*********')

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}

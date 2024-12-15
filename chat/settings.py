from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-&+1%a@-(1o#b7y)i9&*=vv6fg7pycll%$$^!ktwt!8_bz#up17'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

LOGOUT_REDIRECT_URL = 'login_view'
LOGIN_REDIRECT_URL = 'rooms'
LOGIN_URL = 'login_view'

INSTALLED_APPS = [
    'channels',
    'capp',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chat.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Use ASGI for Channels
WSGI_APPLICATION = 'chat.wsgi.application'
ASGI_APPLICATION = 'chat.asgi.application'

# In-memory channel layer for Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
# Database settings (using SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = 'static/'

# Default auto field setting
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Translation settings
NLLB_MODEL = "facebook/nllb-200-distilled-600M"
from capp.flores200_codes import flores_codes

SUPPORTED_LANGUAGES = {v: k for k, v in flores_codes.items()}

# Add these settings for better debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Translation Settings
TRANSLATION_SETTINGS = {
    'ENABLE_ONLINE_SERVICES': False,  # Disable online services
    'PRIMARY_MODEL': 'nllb',
    'FALLBACK_ORDER': ['dictionary'],  # Only use dictionary as fallback
}

# Translation model paths
TRANSLATION_MODELS = {
    'NLLB_PATH': os.path.expanduser("~/.cache/huggingface/hub/models--facebook--nllb-200-distilled-600M"),
    'OPUS_PATH': os.path.expanduser("~/.cache/huggingface/hub/models--Helsinki-NLP--opus-mt-en-sn")
}

# Add to your settings.py

# Add these settings
NLLB_SETTINGS = {
    'MODEL_NAME': 'facebook/nllb-200-distilled-600M',
    'MAX_LENGTH': 400,
    'NUM_BEAMS': 5,
    'EARLY_STOPPING': True
}

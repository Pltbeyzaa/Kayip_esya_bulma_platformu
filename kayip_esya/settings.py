"""
Django settings for kayip_esya project.
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Geliştirme ortamında DisallowedHost hatalarını engellemek için geniş tutuyoruz.
# İstersen production'da .env içine ALLOWED_HOSTS değerini özel olarak yazabilirsin.
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='*,localhost,127.0.0.1,kubernetes.docker.internal'
).split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'accounts',
    # Görüntü eşleştirme servisi (Milvus)
    'image_matching',
    # Konum servisi (Google Maps API → MySQL)
    'location_services',
    # Mesajlaşma servisi (Firebase API → MongoDB)
    'messaging',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kayip_esya.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'kayip_esya.wsgi.application'

# Database Configuration
# MySQL for location data (Google Maps API)
# MongoDB for messaging (Firebase API)
# Milvus for image matching (Google Cloud Vision API)

# MySQL Database (for location data)
MYSQL_DB_NAME = config('MYSQL_DB_NAME', default='findus_locations')
MYSQL_DB_USER = config('MYSQL_DB_USER', default='root')
MYSQL_DB_PASSWORD = config('MYSQL_DB_PASSWORD', default='')
MYSQL_DB_HOST = config('MYSQL_DB_HOST', default='localhost')
MYSQL_DB_PORT = config('MYSQL_DB_PORT', default=3306, cast=int)

# --- DATABASE CONFIGURATION ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('MYSQL_DB_NAME', default='findus_locations'),
        'USER': config('MYSQL_DB_USER', default='root'),
        'PASSWORD': config('MYSQL_DB_PASSWORD', default=''),
        'HOST': config('MYSQL_DB_HOST', default='localhost'),
        'PORT': config('MYSQL_DB_PORT', default=3306, cast=int),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# MongoDB Configuration
MONGODB_URL = config('MONGODB_URL', default='mongodb://localhost:27017/')
MONGODB_DATABASE = config('MONGODB_DATABASE', default='kayip_esya_db')

# Milvus Vector Database Configuration
MILVUS_HOST = config('MILVUS_HOST', default='localhost')
MILVUS_PORT = config('MILVUS_PORT', default=19530, cast=int)
MILVUS_USER = config('MILVUS_USER', default='')
MILVUS_PASSWORD = config('MILVUS_PASSWORD', default='')

# Password validation
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
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# UTF-8 Encoding
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# Locale paths for Turkish
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# API Keys and External Services
GOOGLE_CLOUD_PROJECT_ID = config('GOOGLE_CLOUD_PROJECT_ID', default='')
GOOGLE_APPLICATION_CREDENTIALS = config('GOOGLE_APPLICATION_CREDENTIALS', default='')
GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')

# Firebase Configuration (for messaging/communication)
FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='')
FIREBASE_DATABASE_URL = config('FIREBASE_DATABASE_URL', default='')
FIREBASE_PROJECT_ID = config('FIREBASE_PROJECT_ID', default='')

# Redis Configuration (for Celery)
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

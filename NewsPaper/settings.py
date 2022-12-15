from dotenv import load_dotenv;

from pathlib import Path
import os;


load_dotenv();                                                  # вызовем функцию - подгрузим файлы с переменными окружения


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY");



ALLOWED_HOSTS = [];

DEBUG = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'news',                                     # подключаем основное приложение
    'accounts',                                 # подключаем accounts
    'fpages',
    'django_filters',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.yandex',
    'django_apscheduler',
];

SITE_ID=1;

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
];

ROOT_URLCONF = 'NewsPaper.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],                                          # при обращении будем искать в этих каталогах
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
];


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
];




ACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSignupForm'             # путь до класса кастом-формы регистрации
};




WSGI_APPLICATION = 'NewsPaper.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
};


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
];



APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a";
APSCHEDULER_RUN_NOW_TIMEOUT = 25;

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us';
TIME_ZONE = 'UTC';
USE_I18N = True;
USE_TZ = False;


# CSS, JavaScript, Images
STATIC_URL = 'static/';
STATICFILES_DIRS = [BASE_DIR/"static"];


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_HOST = os.getenv("EMAIL_HOST");
EMAIL_PORT = os.getenv("EMAIL_PORT");
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER");
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD");
EMAIL_USE_SSL = True;
EMAIL_USE_TLS = False;

SERVER_EMAIL = EMAIL_HOST_USER;
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL");

ACCOUNT_AUTHENTICATION_METHOD = 'email';
ACCOUNT_CONFIRM_EMAIL_ON_GET = True;                            # сразу подтверждать регистрацию после перехода по ссылке из письма (не показывать страницу confirm)
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1;                     # сколько дней будет действовать ссылка из письма на подтверждение регистрации
ACCOUNT_EMAIL_REQUIRED = True;                                  # требуется email при регистрации
ACCOUNT_EMAIL_VERIFICATION = 'mandatory';                       # optional - шлет письмо, но подтверждение не обязательно; none - дефолт - не шлет и не требуется
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 3;                               # попытки входа, после которых вход будет "заморожен" на секунды в ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT :
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 86400;
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True;                     # после подтверждения (перехода по ссылке из письма) сразу автоматически выполнять вход
ACCOUNT_LOGIN_REDIRECT_URL = '/news/';
ACCOUNT_LOGOUT_ON_GET = False;                                  # выход из аккаунта без подтверждения, а просто по ссылке типа get (опасно, обойдем эту беду в js)
ACCOUNT_LOGOUT_REDIRECT_URL = '/news/';                         # куда перенаправить после выхода из аккаунта
ACCOUNT_UNIQUE_EMAIL = True;
ACCOUNT_USERNAME_REQUIRED = False;
#ACCOUNT_SIGNUP_PASSWORD_VERIFICATION = False;

LOGIN_REDIRECT_URL = '/news/';
LOGOUT_REDIRECT_URL = '/news/';

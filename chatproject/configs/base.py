# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
import djcelery
from datetime import timedelta

djcelery.setup_loader()

PROJECT_NAME = 'chat'
ADMINS = (('Balkan', 'mburakalkan@gmail.com'), ('bahattincinic', 'bahattincinic@gmail.com'))
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APPS = os.path.join(BASE_DIR, 'apps')
sys.path.insert(1, APPS)
sys.path.insert(2, BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'xv-#91!%mv!(m0yba%t0^1t683mvwj_c!5d1z--^8!2x5z(6ss'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# TEMPLATE CONFIGURATION
# See:
# https://docs.djangoproject.com/en/dev/ref/
# settings/#template-context-processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates')
)
# END TEMPLATE CONFIGURATION

ALLOWED_HOSTS = ["*"]

AUTH_USER_MODEL = 'account.User'

########## MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = os.path.normpath(os.path.join(BASE_DIR, 'media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
AVATAR_MEDIA_URL = MEDIA_URL + 'avatar/'
BACKGROUND_MEDIA_URL = MEDIA_URL + 'cover/'
########## END MEDIA CONFIGURATION

# APP CONFIGURATION
DJANGO_APPS = (
    # Default Django apps:
    #'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
)

THIRD_PARTY_APPS = (
    'django_extensions',
    'rest_framework',
    'djcelery',
    'haystack',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'actstream',
    'account',
    'api',
    'chat',
    'network',
    'page',
    'internal',
    'shuffle',
    'search'
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


# sessions on redis
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 0
SESSION_REDIS_PREFIX = 'djsession'


ROOT_URLCONF = 'chatproject.urls'

WSGI_APPLICATION = 'chatproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Rest Framework Config http://django-rest-framework.org/#installation
REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'auth.authentication.ExpiringTokenAuthentication'
    ),
    # Custom Exception Handler
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',

    'TEST_REQUEST_RENDERER_CLASSES': (
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.JSONRenderer',
    ),
    # Pagination settings
    'PAGINATE_BY': 10,
    'PAGINATE_BY_PARAM': 'page_size',
    'MAX_PAGINATE_BY': 100,
}

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1",
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

# Celery Config
BROKER_URL = "amqp://guest:guest@localhost:5672//"

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_FROM_EMAIL = "sentry@burakalkan.com"

# EMAIL_BACKEND = 'core.mail.backends.CeleryEmailBackend'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

########## STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = os.path.normpath(os.path.join(BASE_DIR, 'static'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See:https://docs.djangoproject.com/en/dev/ref/contrib
#       /staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    os.path.normpath(os.path.join(BASE_DIR, 'chat_static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib
#       /staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
########## END STATIC FILE CONFIGURATION

# Devices
DESKTOP = 'desktop'
MOBILE = 'mobile'
IOS = 'ios'
ANDROID = 'android'
DEVICE_CHOCIES = ((DESKTOP, 'Desktop'), (IOS, 'ios'),
                  (ANDROID, 'Android'), (MOBILE, 'Mobile'))

AUTH_SESSION = 'authsession'
TOKEN_SESSION = 'tokensession'
AUTH_TYPES = ((AUTH_SESSION, 'Auth Session'), (TOKEN_SESSION, 'Token Session'))

# Api
API_VERSION = 'v1'
API_ALLOWED_FORMATS = ['json']
# 15 days
API_TOKEN_TTL = 15

# DJANGO-STATIC config
DJANGO_STATIC = False
DJANGO_STATIC_SAVE_PREFIX = "/tmp/cache"
DJANGO_STATIC_NAME_PREFIX = "/cache"
DJANGO_STATIC_MEDIA_ROOTS = (BASE_DIR,)
# WHITESPACE_ONLY, SIMPLE_OPTIMIZATIONS, ADVANCED_OPTIMIZATIONS
# wh: 308k, simple: 260k, advanced: 224k ERRORS!!
DJANGO_STATIC_CLOSURE_COMPILER_COMP_LEVEL = 'WHITESPACE_ONLY'
DJANGO_STATIC_CLOSURE_COMPILER_IGNORE_WARNINGS = True
DJANGO_STATIC_CLOSURE_COMPILER = '%s/../deploy/compiler.jar' % BASE_DIR
DJANGO_STATIC_FILENAME_GENERATOR = 'utils.gen'

INTERNAL_ALLOWED = ('127.0.0.1', '127.0.1.1', '192.168.75.1',
                    '192.168.0.11', '188.226.199.124')
REDIS_RANK_KEY = 'active_connections'
REDIS_RANK_MAX_USERS = 20
# by default on local
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
}

# realtime updates
HAYSTACK_SIGNAL_PROCESSOR = 'search.signal_processor.QueuedSignalProcessor'

# celery setting
BROKER_URL = 'amqp://guest@localhost//'
CELERY_TIMEZONE = 'UTC'

# celery routes
CELERY_ROUTES = {
    'search.tasks.update_index': {
        'queue': 'haystack'
    },
    'search.tasks.save_search_query': {
        'queue': 'haystack'
    }
}

# beat
CELERYBEAT_SCHEDULE = {
    'reindex_all': {
        'task': 'search.tasks.reindex_all',
        'schedule': timedelta(hours=4),
        'args': ()
    }
}

# search
SEARCH_LIMIT = 5
SEARCH_QUERY_LENGTH = 2

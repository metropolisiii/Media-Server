"""
 Django settings for media_server project.
 These settings are used for PRODUCTION
 There is a separate dev_settings.py file for DEVELOPMENT
 Specify the correct settings file in wsgi.py and apache/django.wsgi
"""

import socket
DEBUG = True
import os.path
import django.conf.global_settings as DEFAULT_SETTINGS


TEMPLATE_DEBUG = False

ADMINS = (
    ('Jason Kirby', 'j.smith@Mycompany.com'),
)

MANAGERS = ADMINS

#Enable get_profile functionality
AUTH_PROFILE_MODULE = 'media.UserProfile'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'media_server',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'django',
        'PASSWORD': 'password',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

VIDEO_TYPES = {'image/jpeg':'jpg', 'audio/mpeg':'mp3', 'video/x-flv':'flv', 'video/mp4':'mp4', 'video/x-ms-wmv':'wmv', 'video/x-ms-asf':'wmv', 'video/x-msvideo':'avi', 'video/avi':'avi','video/webm':'webm'}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['Mycompanytv.Mycompany.com']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Denver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_user = '/var/www/media_server/static/media/'

# URL that handles the media served from MEDIA_user. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/static/media/'
TASK_UPLOAD_FILE_TYPES = ['mp4','video/mp4']
TASK_UPLOAD_FILE_MAX_SIZE = "52428800000"
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_user = '/var/www/media_server/static/'
# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/login/'
LOGFILE='/var/django-apps/Mycompanytv/logs/logfile'
# Additional locations of static files
STATICFILES_DIRS = (
	#"/var/www/media_server/static",
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '+mja97a*j_ydn&#jy3x-7y(f-s16t!$erx0d(=p4qnkuo-8-hp'
CROWD_URL = 'http://tstauth.Mycompanytest.com:8095/crowd/'
CROWD_USER = 'Mycompanytv'
CROWD_PASSWORD = 'password'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(os.path.dirname(__file__), 'templates'),
        ],
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
				'django.template.context_processors.request',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
				'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

user_URLCONF = 'media_server.urls'
X_FRAME_OPTIONS = 'EXEMPT'
#LDAP SETUP
AUTHENTICATION_BACKENDS = (
	#'crowd.backend.CrowdBackend',
	'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)
AUTH_LDAP_SERVER_URI = "ldap://ldap.Mycompany.com"
import ldap
from django_auth_ldap.config import LDAPSearch

AUTH_LDAP_BIND_DN = "CN=mediasrv,CN=users, DC=Mycompany,DC=com"
AUTH_LDAP_BIND_PASSWORD = "password"
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=community,dc=Mycompany,dc=com",ldap.SCOPE_SUBTREE, "(sAMAccountName=%(user)s)")
AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn","username":"sAMAccountName","email":"mail","photo":"thumbnailPhoto"}	
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0
}
#AUTH_CROWD_STAFF_GROUP = 'staff'
#AUTH_CROWD_SUPERUSER_GROUP = 'superuser'
#AUTH_CROWD_APPLICATION_USER = 'django'
#AUTH_CROWD_APPLICATION_PASSWORD = 'test'
#AUTH_CROWD_SERVER_URI = 'http://tstauth.Mycompany.com:8095/crowd/services/SecurityServer?wsdl'

import logging

logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


BROKER_URL = "amqp://guest@localhost:5672/"

CELERY_IMPORTS = ("media.tasks",)

CELERY_RESULT_BACKEND = "amqp"

CELERY_ANNOTATIONS = {"*": {"rate_limit": "10/s"}}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
	'django_extensions',
	'media',
	'ajax_validation',
	'el_pagination',
	'rest_framework',
	'rest_framework.authtoken',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
	'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ]
}


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'stream_to_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django_auth_ldap': {
            'handlers': ['stream_to_console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

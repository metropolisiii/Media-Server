import os
import sys
path = '/var/django-apps/Mycompanytv'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'media_server.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()



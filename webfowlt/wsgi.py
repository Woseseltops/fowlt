import os, sys
sys.path.append('/var/www/valkuil/webvalkuil/')
sys.path.append('/var/www/valkuil/')
os.environ['PYTHONPATH'] = '/var/www/valkuil/'

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

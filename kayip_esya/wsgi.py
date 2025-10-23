"""
WSGI config for kayip_esya project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')

application = get_wsgi_application()

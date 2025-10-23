"""
ASGI config for kayip_esya project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayip_esya.settings')

application = get_asgi_application()

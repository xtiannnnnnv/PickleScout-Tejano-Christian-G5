"""
ASGI config for PickleScout project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'picklescout.settings')
application = get_asgi_application()

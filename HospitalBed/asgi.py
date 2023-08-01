"""
ASGI config for HospitalBed project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from HospitalBed import initial_data, apscheduler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalBed.settings')

application = get_asgi_application()

initial_data.initialize()
apscheduler.start()

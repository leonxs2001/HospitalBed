"""
WSGI config for HospitalBed project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from HospitalBed import apscheduler, initial_data

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalBed.settings')

application = get_wsgi_application()

initial_data.initialize()
apscheduler.start()


import datetime

from django.shortcuts import render

# Create your views here.
from dashboard.models import Stay, Visit
from dashboard.services.hl7_services import parse_all_hl7_messages


def test(request):
    parse_all_hl7_messages()


def test2(request):
    Visit.objects.filter(visit_id=1).last().delete()
    print()

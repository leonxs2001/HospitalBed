import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict

from django.db import models
from django.utils import timezone

from dashboard.models import hospital_models

DATE_FORMAT = "%Y-%m-%dT%H:%M"
GERMAN_DATE_FORMAT = "%d.%m.%Y %H:%M Uhr"


class ModelJSONEncoder(DjangoJSONEncoder):
    """DjangoJSONEncoder for including the models and QuerySets"""
    def default(self, o):
        if isinstance(o, models.QuerySet):
            return list(o.values())
        if isinstance(o, models.Model):
            return model_to_dict(o)
        if isinstance(o, timezone.datetime):
            return o.strftime(DATE_FORMAT)
        return super(ModelJSONEncoder, self).default(o)


def get_sex_from_location(location):
    """Returns the right string representation of the sex based on number attributes of a given location."""
    if location.number_of_men > 0:
        return hospital_models.Patient.SexChoices.MALE
    elif location.number_of_women > 0:
        return hospital_models.Patient.SexChoices.FEMALE
    elif location.number_of_diverse > 0:
        return hospital_models.Patient.SexChoices.DIVERSE
    else:
        return "Leer"

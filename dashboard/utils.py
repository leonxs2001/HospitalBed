import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict

from django.db import models
from django.utils import timezone

DATE_FORMAT = "%Y-%m-%dT%H:%M"
GERMAN_DATE_FORMAT = "%d.%m.%Y %H:%M Uhr"


class ModelJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, models.QuerySet):
            return list(o.values())
        if isinstance(o, models.Model):
            return model_to_dict(o)
        if isinstance(o, timezone.datetime):
            return o.strftime(DATE_FORMAT)
        return super(ModelJSONEncoder, self).default(o)

import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict

from django.db import models

DATE_FORMAT = "%Y-%m-%dT%H:%M"


class ModelJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, models.QuerySet):
            return list(o.values())
        if isinstance(o, models.Model):
            return model_to_dict(o)
        if isinstance(o, datetime.datetime):
            return o.strftime(DATE_FORMAT)
        return super(ModelJSONEncoder, self).default(o)

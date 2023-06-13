import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict

from django.db import models


class ModelJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, models.QuerySet):
            return [model_to_dict(model_object) for model_object in o]
        if isinstance(o, models.Model):
            return model_to_dict(o)
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%dT%H:%M")
        return super(ModelJSONEncoder, self).default(o)
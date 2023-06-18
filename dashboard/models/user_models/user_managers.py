import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import models

from dashboard.models.hospital_models import hospital_models
from dashboard.models.user_models import user_models

class DataRepresentationManager(models.Manager):
    def structured_data_representations(self):
        structured_result = dict()
        data_representations = self.all()

        for data_representation in data_representations:
            location_dict = dict()
            if data_representation.location_type in structured_result:
                location_dict = structured_result[data_representation.location_type]
            else:
                structured_result[data_representation.location_type] = location_dict

            theme_set = set()
            if data_representation.theme_type in location_dict:
                theme_set = location_dict[data_representation.theme_type]
            else:
                location_dict[data_representation.theme_type] = theme_set

            theme_set.add(data_representation)

        return structured_result


class UserDataRepresentationManager(models.Manager):
    def create_user_data_representation(self, data_representation, user):
        time = None
        end_time = None
        ward = None
        room = None
        # TODO was wenn nichts gegeben, weil leer? --> beim get?
        if data_representation.time_type == user_models.DataRepresentation.TimeChoices.TIME:
            time = datetime.datetime.now()
        elif data_representation.time_type == user_models.DataRepresentation.TimeChoices.PERIOD:
            time = datetime.datetime.now() - datetime.timedelta(weeks=4)
            end_time = datetime.datetime.now(tz=ZoneInfo(settings.TIME_ZONE))

        if data_representation.location_type == user_models.DataRepresentation.LocationChoices.WARD:
            ward = hospital_models.Ward.objects.first()
        elif data_representation.location_type == user_models.DataRepresentation.LocationChoices.ROOM:
            room = hospital_models.Room.objects.first()

        max_order = max_order = user_models.UserDataRepresentation.objects.aggregate(max_order=models.Max('order'))['max_order']
        new_order = 0
        if max_order != None:
            new_order = max_order + 1

        return self.create(time=time, end_time=end_time, order=new_order,
                           user=user, data_representation=data_representation,
                           ward=ward, room=room)


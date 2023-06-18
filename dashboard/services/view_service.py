import datetime

from dashboard.models.user_models import user_models
from dashboard.models.hospital_models import hospital_models


# todo klassen service
# todo vlt doch in model?
def get_locations_for_time(user_data_representation: user_models.UserDataRepresentation, location_type: str,
                           time_type: str, now: datetime.datetime):
    if location_type != user_models.DataRepresentation.LocationChoices.HOSPITAL:
        location_class = None
        if location_type == user_models.DataRepresentation.LocationChoices.WARD:
            location_class = hospital_models.Ward
        elif location_type == user_models.DataRepresentation.LocationChoices.ROOM:
            location_class = hospital_models.Room

        if time_type == user_models.DataRepresentation.TimeChoices.TIME:
            return location_class.objects.filter_for_time(user_data_representation.time)
        elif time_type == user_models.DataRepresentation.TimeChoices.PERIOD:
            return location_class.objects.filter_for_period(user_data_representation.time,
                                                            user_data_representation.end_time)
        else:
            return location_class.objects.filter_for_time(now)
    else:
        return None


def set_new_user_data_representation_location(user_data_representation: user_models.UserDataRepresentation,
                                              location_type: str):
    if location_type == user_models.DataRepresentation.LocationChoices.WARD:
        user_data_representation.ward_id = hospital_models.Ward.objects.values("id").last()["id"]
    elif location_type == user_models.DataRepresentation.LocationChoices.ROOM:
        user_data_representation.room_id = hospital_models.Room.objects.values("id").last()["id"]

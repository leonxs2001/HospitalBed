import datetime
from zoneinfo import ZoneInfo

from HospitalBed import settings
from dashboard.models import UserDataRepresentation, DataRepresentation, Department, Ward, Room


# todo klassen service
def get_locations_for_time(user_data_representation: UserDataRepresentation, location_type: str, time_type: str):
    if location_type != DataRepresentation.LocationChoices.HOSPITAL:
        location_class = None
        if location_type == DataRepresentation.LocationChoices.DEPARTMENT:
            location_class = Department
        elif location_type == DataRepresentation.LocationChoices.WARD:
            location_class = Ward
        elif location_type == DataRepresentation.LocationChoices.ROOM:
            location_class = Room

        if time_type == DataRepresentation.TimeChoices.TIME:
            return location_class.objects.filter_for_time(user_data_representation.time)
        elif time_type == DataRepresentation.TimeChoices.PERIOD:
            return location_class.objects.filter_for_period(user_data_representation.time,
                                                            user_data_representation.end_time)
        else:
            return location_class.objects.filter_for_time(
                datetime.datetime.now(tz=ZoneInfo(settings.TIME_ZONE)))
    else:
        return None

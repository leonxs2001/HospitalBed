import datetime
import csv
import io
from tempfile import SpooledTemporaryFile

from django.http import HttpResponse

from dashboard.models.user_models import user_models
from dashboard.models.hospital_models import hospital_models

# todo klassen service
# todo vlt doch in model?
from dashboard.models.user_models.user_models import DataRepresentation
from dashboard.utils import GERMAN_DATE_FORMAT


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
        return []


def set_new_user_data_representation_location(user_data_representation: user_models.UserDataRepresentation,
                                              location_type: str):
    if location_type == user_models.DataRepresentation.LocationChoices.WARD:
        user_data_representation.ward_id = hospital_models.Ward.objects.values("id").last()["id"]
    elif location_type == user_models.DataRepresentation.LocationChoices.ROOM:
        user_data_representation.room_id = hospital_models.Room.objects.values("id").last()["id"]


def create_csv_file_response(context, location_type, theme_type, time_type):
    filename = generate_csv_file_name_from_context(context, location_type, theme_type, time_type)
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    data = context["data"]

    writer = csv.writer(response, dialect='excel', delimiter=';')

    if theme_type == DataRepresentation.ThemeChoices.INFORMATION:
        if location_type == DataRepresentation.LocationChoices.ROOM:
            room = data[0]
            writer.writerow(["Geschlecht", "Durchschnittliches Alter", "Freie Betten", "Auslastung in %"])
            writer.writerow([get_sex_from_location(room), room.average_age, room.max_number - room.number,
                            room.occupancy])
        elif location_type == DataRepresentation.LocationChoices.WARD:
            ward = data[0]
            writer.writerow(["Anzahl Betten", "Belegte Betten", "Leere Betten", "Auslastung in %", "Anzahl Maenner",
                            "Anzahl Frauen", "Anzahl Diverse"])
            writer.writerow([ward.max_number, ward.number, ward.max_number - ward.number, ward.occupancy,
                            ward.number_of_men, ward.number_of_women, ward.number_of_diverse])

    return response


def generate_csv_file_name_from_context(context, location_type, theme_type, time_type):
    user_data_representation = context["user_data_representation"]
    result = ""

    if theme_type == DataRepresentation.ThemeChoices.INFORMATION:
        result = "Informationen "
    elif theme_type == DataRepresentation.ThemeChoices.HISTORY:
        result = "Verlauf "
    elif theme_type == DataRepresentation.ThemeChoices.ALL_WARDS:
        result = "Stationen "
    elif theme_type == DataRepresentation.ThemeChoices.ALL_ROOMS:
        result = "Zimmer "
    elif theme_type == DataRepresentation.ThemeChoices.ALL_BEDS:
        result = "Betten "

    if location_type == DataRepresentation.LocationChoices.HOSPITAL:
        result += "des Krankenhauses"
    elif location_type == DataRepresentation.LocationChoices.WARD:
        name = hospital_models.Ward.objects.values_list("name", flat=True).get(id=user_data_representation.ward_id)
        result += "der Station " + name
    elif location_type == DataRepresentation.LocationChoices.ROOM:
        name = hospital_models.Room.objects.values_list("name", flat=True).get(id=user_data_representation.room_id)
        result += "des Zimmers " + name

    result += " vom "

    if time_type == DataRepresentation.TimeChoices.NEARTIME:
        result += datetime.datetime.now().strftime(GERMAN_DATE_FORMAT)
    else:
        result += user_data_representation.time.strftime(GERMAN_DATE_FORMAT)
        if time_type == DataRepresentation.TimeChoices.PERIOD:
            result += "bis zum "
            result += user_data_representation.end_time.strftime(GERMAN_DATE_FORMAT)
    result += ".csv"
    return result


def get_sex_from_location(location):  # TODO throw exception, if it has no number of men
    if location.number_of_men > 0:
        return hospital_models.Patient.SexChoices.MALE
    elif location.number_of_women > 0:
        return hospital_models.Patient.SexChoices.FEMALE
    else:  # TODO denke drüber nache, welehces geshclecht, falls leer!
        return hospital_models.Patient.SexChoices.DIVERSE


def is_location_id_in_locations(ID, locations):
    for location in locations:
        if location.id == ID:
            return True
    return False


import csv
import datetime
from abc import ABC, abstractmethod
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Manager
from django.http import JsonResponse, FileResponse, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from dashboard.models import DataRepresentation, UserDataRepresentation, hospital_models
from dashboard.models.hospital_models import Bed
from dashboard.utils import ModelJSONEncoder, DATE_FORMAT, GERMAN_DATE_FORMAT, get_sex_from_location

from django.db.utils import IntegrityError


class DataGenerator(ABC):
    @abstractmethod
    def generate_data(self, user_data_representation, manager):
        pass


class LocationInformationGenerator(DataGenerator, ABC):

    def generate_data(self, user_data_representation, manager):
        data_representation = user_data_representation.data_representation
        query_set = self.get_query_set(user_data_representation, manager)

        if data_representation.time_type == DataRepresentation.TimeChoices.PERIOD:
            return query_set.information_for_period(user_data_representation.time,
                                                    user_data_representation.end_time)
        elif data_representation.time_type == DataRepresentation.TimeChoices.TIME:
            return query_set.information_for_time(user_data_representation.time)
        else:
            return query_set.information_for_time(timezone.now())

    @abstractmethod
    def get_query_set(self, user_data_representation, manager: Manager):
        pass


class SingleLocationInformationGenerator(LocationInformationGenerator):

    def get_query_set(self, user_data_representation, manager):
        location_id = user_data_representation.location_id
        return manager.filter_for_id(location_id)


class HospitalInformationGenerator(LocationInformationGenerator):
    def get_query_set(self, user_data_representation, manager):
        return manager.all()


class MultipleLocationsInformationGenerator(LocationInformationGenerator):

    def get_query_set(self, user_data_representation, manager):
        data_representation = user_data_representation.data_representation

        if data_representation.location_type == DataRepresentation.LocationChoices.HOSPITAL:
            return manager.all()
        else:
            location_id = user_data_representation.location_id
            if data_representation.location_type == DataRepresentation.LocationChoices.WARD:
                return manager.all_from_ward(location_id)
            elif data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
                return manager.all_from_room(location_id)


class LocationHistoryGenerator(DataGenerator, ABC):

    def generate_data(self, user_data_representation: UserDataRepresentation, manager):
        context = dict()
        start = user_data_representation.time
        end = user_data_representation.end_time

        query_set = self.get_query_set(user_data_representation, manager)

        for time in (start + ((end - start) / 9) * n for n in range(10)):
            context[time.strftime(DATE_FORMAT)] = query_set.occupancy(time)

        return context


class SingleLocationHistoryGenerator(LocationHistoryGenerator):

    def get_query_set(self, user_data_representation, manager):
        location_id = user_data_representation.location_id
        return manager.filter_for_id(location_id)


class HospitalHistoryGenerator(LocationHistoryGenerator):
    def get_query_set(self, user_data_representation, manager):
        return hospital_models.Bed.hospital_objects.all()


class DataGeneratorFactory:
    @staticmethod
    def create_data_generator(data_representation):
        if data_representation.theme_type == DataRepresentation.ThemeChoices.INFORMATION:
            if data_representation.location_type == DataRepresentation.LocationChoices.HOSPITAL:
                return HospitalInformationGenerator()
            else:

                return SingleLocationInformationGenerator()
        elif data_representation.theme_type == DataRepresentation.ThemeChoices.HISTORY:
            if data_representation.location_type == DataRepresentation.LocationChoices.HOSPITAL:
                return HospitalHistoryGenerator()
            else:

                return SingleLocationHistoryGenerator()
        else:
            return MultipleLocationsInformationGenerator()

    @staticmethod
    def generate_csv_file_response(data, user_data_representation):
        data_representation = user_data_representation.data_representation
        # generate filename
        filename = ""
        if data_representation.theme_type == DataRepresentation.ThemeChoices.INFORMATION:
            filename = "Informationen "
        elif data_representation.theme_type == DataRepresentation.ThemeChoices.HISTORY:
            filename = "Verlauf "
        elif data_representation.theme_type == DataRepresentation.ThemeChoices.ALL_WARDS:
            filename = "Stationen "
        elif data_representation.theme_type == DataRepresentation.ThemeChoices.ALL_ROOMS:
            filename = "Zimmer "
        elif data_representation.theme_type == DataRepresentation.ThemeChoices.ALL_BEDS:
            filename = "Betten "

        if data_representation.location_type == DataRepresentation.LocationChoices.HOSPITAL:
            filename += "des Krankenhauses"
        elif data_representation.location_type == DataRepresentation.LocationChoices.WARD:
            name = hospital_models.Ward.objects.values_list("name", flat=True).get(id=user_data_representation.ward_id)
            filename += "der Station " + name
        elif data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
            name = hospital_models.Room.objects.values_list("name", flat=True).get(id=user_data_representation.room_id)
            filename += "des Zimmers " + name

        filename += " vom "

        if data_representation.time_type == DataRepresentation.TimeChoices.NEARTIME:
            filename += timezone.now().strftime(GERMAN_DATE_FORMAT)
        else:
            filename += user_data_representation.time.strftime(GERMAN_DATE_FORMAT)
            if data_representation.time_type == DataRepresentation.TimeChoices.PERIOD:
                filename += "bis zum "
                filename += user_data_representation.end_time.strftime(GERMAN_DATE_FORMAT)
        filename += ".csv"

        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

        writer = csv.writer(response, dialect='excel', delimiter=';')
        if data_representation.theme_type == DataRepresentation.ThemeChoices.HISTORY:
            pass
        elif data_representation.theme_type == DataRepresentation.ThemeChoices.INFORMATION:
            if data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
                writer.writerow(
                    ["Geschlecht", "Durchschnittliches Alter", "Anzahl Betten", "Belegte Betten"])
                room = data[0]
                writer.writerow([get_sex_from_location(room), room.average_age, room.max_number, room.number])
            elif data_representation.location_type == DataRepresentation.LocationChoices.WARD:
                writer.writerow(["Anzahl Betten", "Belegte Betten", "Anzahl Maenner",
                                 "Anzahl Frauen", "Anzahl Diverse"])
                ward = data[0]
                writer.writerow(
                    [ward.max_number, ward.number, ward.number_of_men, ward.number_of_women, ward.number_of_diverse])
            else:
                writer.writerow(["Anzahl Betten", "Belegte Betten", "Anzahl Maenner",
                                 "Anzahl Frauen", "Anzahl Diverse"])
                max_number = data["max_number"]
                number = data["number"]
                writer.writerow(
                    [max_number, number, data["number_of_men"], data["number_of_women"], data["number_of_diverse"]])
        else:
            if data_representation.theme_type == DataRepresentation.ThemeChoices.ALL_ROOMS:
                writer.writerow(["ID", "Geschlecht", "Durchschnittliches Alter", "Anzahl Betten", "Belegte Betten"])
                for room in data:
                    writer.writerow(
                        [room.id, get_sex_from_location(room), room.average_age, room.max_number, room.number])
            elif data_representation.theme_type == DataRepresentation.ThemeChoices.ALL_WARDS:
                writer.writerow(
                    ["ID", "Anzahl Betten", "Belegte Betten",
                     "Anzahl Maenner", "Anzahl Frauen", "Anzahl Diverse"])
                for ward in data:
                    writer.writerow([ward.id, ward.max_number, ward.number, ward.number_of_men, ward.number_of_women,
                                     ward.number_of_diverse])
            else:
                writer.writerow(
                    ["ID", "Alter", "Geschlecht"])
                for bed in data:
                    writer.writerow([bed.id, bed.average_age, get_sex_from_location(bed)])

        return response


class LocationDataResponseView(View):

    @method_decorator(login_required)
    def get(self, request, location_type, theme_type, time_type):
        user_data_representation = UserDataRepresentation.objects.select_related('data_representation').get(
            id=request.GET["id"])
        locations = None

        if request.GET["update_flag"] == "true":
            changed = False

            if time_type == DataRepresentation.TimeChoices.TIME:
                changed = True
                user_data_representation.time = timezone.datetime.strptime(request.GET["time"], DATE_FORMAT)
            elif time_type == DataRepresentation.TimeChoices.PERIOD:
                changed = True
                user_data_representation.time = timezone.datetime.strptime(request.GET["time"], DATE_FORMAT)
                user_data_representation.end_time = timezone.datetime.strptime(request.GET["end_time"], DATE_FORMAT)

            locations = user_data_representation.locations

            if location_type != DataRepresentation.LocationChoices.HOSPITAL:
                changed = True
                location_id = request.GET["location_id"]
                # set locationId to a random value (or None), if the location id does not exists in locatiosn
                id_in_locations = False
                for location in locations:
                    if location.id == location_id:
                        id_in_locations = True
                        break

                if not id_in_locations:
                    if len(locations) > 0:
                        location_id = locations[0].id
                    else:
                        location_id = None

                if location_type == DataRepresentation.LocationChoices.WARD:
                    user_data_representation.ward_id = location_id
                elif location_type == DataRepresentation.LocationChoices.ROOM:
                    user_data_representation.room_id = location_id

            if changed:
                try:
                    user_data_representation.save()
                except IntegrityError:
                    data_representation = user_data_representation.data_representation
                    if data_representation.location_type == DataRepresentation.LocationChoices.WARD:
                        user_data_representation.ward_id = hospital_models.Ward.objects.values("id").last()["id"]
                    elif data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
                        user_data_representation.room_id = hospital_models.Room.objects.values("id").last()["id"]
                    user_data_representation.save()

        data_generator = DataGeneratorFactory.create_data_generator(user_data_representation.data_representation)

        context = dict()
        manager = user_data_representation.data_representation.location_manager
        data = data_generator.generate_data(user_data_representation, manager)
        context["data"] = data
        context["user_data_representation"] = UserDataRepresentation.objects.get(id=request.GET["id"])

        if request.GET["download"] == "true":
            return DataGeneratorFactory.generate_csv_file_response(data, user_data_representation)

        else:
            # get locations if not already got
            if locations is None:
                locations = user_data_representation.locations

            if locations:
                context["locations"] = locations
            return JsonResponse(context, ModelJSONEncoder)

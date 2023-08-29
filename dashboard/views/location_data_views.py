import csv
from abc import ABC, abstractmethod

from django.contrib.auth.decorators import login_required
from django.db.models import Manager
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from dashboard.models import DataRepresentation, UserDataRepresentation, hospital_models
from dashboard.utils import ModelJSONEncoder, DATE_FORMAT, GERMAN_DATE_FORMAT, get_sex_from_location

from django.db.utils import IntegrityError


class DataGenerator(ABC):
    """Strategy interface for the generation of the data."""

    @abstractmethod
    def generate_data(self, user_data_representation, manager):
        """Returns the right data for the UserDataRepresentation."""
        pass


class LocationInformationGenerator(DataGenerator, ABC):
    """Strategy for the generation of information data."""

    def generate_data(self, user_data_representation, manager):
        data_representation = user_data_representation.data_representation

        # calling the template method
        query_set = self.get_query_set(user_data_representation, manager)

        # perform the right operation with the right parameters on the query_set
        # based on the time_type from the given UserDataRepresentation
        if data_representation.time_type == DataRepresentation.TimeChoices.PERIOD:
            return query_set.information_for_period(user_data_representation.time,
                                                    user_data_representation.end_time)
        elif data_representation.time_type == DataRepresentation.TimeChoices.TIME:
            return query_set.information_for_time(user_data_representation.time)
        else:
            return query_set.information_for_time(timezone.now())

    @abstractmethod
    def get_query_set(self, user_data_representation, manager: Manager):
        """Returns the right QuerySet to perform the operations on."""
        pass


class SingleLocationInformationGenerator(LocationInformationGenerator):
    """Strategy for the generation of information data for a single location."""

    def get_query_set(self, user_data_representation, manager):
        location_id = user_data_representation.location_id
        return manager.filter_for_id(location_id)


class HospitalInformationGenerator(LocationInformationGenerator):
    """Strategy for the generation of information data for the whole hospital."""

    def get_query_set(self, user_data_representation, manager):
        return manager.all()


class MultipleLocationsInformationGenerator(LocationInformationGenerator):
    """Strategy for the generation of information data for multiple locations."""

    def get_query_set(self, user_data_representation, manager):
        data_representation = user_data_representation.data_representation

        # filter the QuerySet of locations based on the location_type from the given UserDataRepresentation
        if data_representation.location_type == DataRepresentation.LocationChoices.HOSPITAL:
            return manager.all()
        else:
            location_id = user_data_representation.location_id
            if data_representation.location_type == DataRepresentation.LocationChoices.WARD:
                return manager.all_from_ward(location_id)
            elif data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
                return manager.all_from_room(location_id)


class LocationHistoryGenerator(DataGenerator, ABC):
    """Strategy for the generation of occupancy history data."""

    def generate_data(self, user_data_representation: UserDataRepresentation, manager):
        context = dict()
        start = user_data_representation.time
        end = user_data_representation.end_time

        # calling the template method
        query_set = self.get_query_set(user_data_representation, manager)

        # go through 10 times from start to end and generate the occupancy for these times
        # they are organised in a dictionary with the formatted times as keys
        for time in (start + ((end - start) / 9) * n for n in range(10)):
            context[time.strftime(DATE_FORMAT)] = query_set.occupancy(time)

        return context

    @abstractmethod
    def get_query_set(self, user_data_representation, manager: Manager):
        """Returns the right QuerySet to perform the operations on."""
        pass


class SingleLocationHistoryGenerator(LocationHistoryGenerator):
    """Strategy for the generation of occupancy history data for a single location."""

    def get_query_set(self, user_data_representation, manager):
        location_id = user_data_representation.location_id
        return manager.filter_for_id(location_id)


class HospitalHistoryGenerator(LocationHistoryGenerator):
    """Strategy for the generation of occupancy history data for the whole hospital."""

    def get_query_set(self, user_data_representation, manager):
        return hospital_models.Bed.hospital_objects.all()


class DataGeneratorFactory:
    """
    Factory for the right DataGenerator strategy based on a DataRepresentation
    and the HttpResponse for a download of a given data as csv file.
    """

    @staticmethod
    def create_data_generator(data_representation):
        """
        Returns the right DataGenerator strategy based on the location_type and theme_type
        from a given DataRepresentation.
        """

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
        """Creates and returns a HttpResponse with a csv file containing the given data in it."""

        data_representation = user_data_representation.data_representation

        # generate the filename based on the given UserDataRepresentation
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

        # create the HttpResponse with the right content_type and headers
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

        # create a writer object for csv file in the HttpResponse
        # use the dialect 'excel' and the delimiter ';' so that the file can be opened with excel
        writer = csv.writer(response, dialect='excel', delimiter=';')

        # fill the csv file with the right data
        if data_representation.theme_type == DataRepresentation.ThemeChoices.HISTORY:
            writer.writerow(["Zeitpunkt", "Anzahl Betten", "Belegte Betten"])
            for formatted_time, location_dict in data.items():
                writer.writerow([formatted_time, location_dict["number"], location_dict["max_number"]])
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
    """View for dynamically returning the requested data to the template."""

    @method_decorator(login_required)
    def get(self, request, location_type, theme_type, time_type):
        """Returns the right data in a HttpResponse for the template and Updates the UserDataRepresentation"""

        user_data_representation = UserDataRepresentation.objects.select_related('data_representation').get(
            id=request.GET["id"])
        locations = None

        # update the UserDataRepresentation if the update_flag is set in the request get parameters
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

            # save the UserDataRepresentation if changes
            if changed:
                try:
                    user_data_representation.save()
                except IntegrityError:
                    data_representation = user_data_representation.data_representation

                    # set some location to the location attributes
                    # of the UserDataRepresentation if there is a IntegrityError
                    # and save it again
                    if data_representation.location_type == DataRepresentation.LocationChoices.WARD:
                        user_data_representation.ward_id = hospital_models.Ward.objects.values("id").last()["id"]
                    elif data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
                        user_data_representation.room_id = hospital_models.Room.objects.values("id").last()["id"]
                    user_data_representation.save()

        # get the DataGenerator strategy from the factory method
        data_generator = DataGeneratorFactory.create_data_generator(user_data_representation.data_representation)

        context = dict()
        manager = user_data_representation.data_representation.location_manager

        # generate the data for the context
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

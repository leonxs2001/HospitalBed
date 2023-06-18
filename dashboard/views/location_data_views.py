import datetime
from abc import ABC, abstractmethod
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Manager
from django.http import JsonResponse
from django.views import View

from dashboard.models.user_models import user_models
from dashboard.models.hospital_models import hospital_models
from dashboard.services.view_service import get_locations_for_time, set_new_user_data_representation_location
from dashboard.utils import ModelJSONEncoder, DATE_FORMAT

from django.db.utils import IntegrityError


class LocationDataResponseView(View, ABC):
    location_type = ""
    theme_type = ""
    time_type = ""

    def get(self, request):
        user_data_representation = user_models.UserDataRepresentation.objects.get(id=request.GET["id"])
        if request.GET["update_flag"] == "true":
            changed = False

            if self.location_type != user_models.DataRepresentation.LocationChoices.HOSPITAL:
                changed = True
                location_id = request.GET["location_id"]
                if self.location_type == user_models.DataRepresentation.LocationChoices.WARD:
                    user_data_representation.ward_id = location_id
                elif self.location_type == user_models.DataRepresentation.LocationChoices.ROOM:
                    user_data_representation.room_id = location_id

            if self.time_type == user_models.DataRepresentation.TimeChoices.TIME:
                changed = True
                user_data_representation.time = datetime.datetime.strptime(request.GET["time"], DATE_FORMAT)
            elif self.time_type == user_models.DataRepresentation.TimeChoices.PERIOD:
                changed = True
                user_data_representation.time = datetime.datetime.strptime(request.GET["time"], DATE_FORMAT)
                user_data_representation.end_time = datetime.datetime.strptime(request.GET["end_time"], DATE_FORMAT)

            if changed:
                try:
                    user_data_representation.save()
                except IntegrityError:
                    set_new_user_data_representation_location(user_data_representation, self.location_type)
                    user_data_representation.save()

        context = self.get_context(request, user_data_representation)
        context["user_data_representation"] = user_models.UserDataRepresentation.objects.get(id=request.GET["id"])

        now = datetime.datetime.now(tz=ZoneInfo(settings.TIME_ZONE))
        locations = get_locations_for_time(user_data_representation, self.location_type, self.time_type, now)
        if locations:
            context["locations"] = locations

        if "download" in request.GET:
            # TODO do download stuff
            pass
        else:
            return JsonResponse(context, ModelJSONEncoder)

    @abstractmethod
    def get_context(self, request, user_data_representation):
        pass


class LocationInformationView(LocationDataResponseView, ABC):

    def get_context(self, request, user_data_representation: user_models.UserDataRepresentation):

        now = datetime.datetime.now(tz=ZoneInfo(settings.TIME_ZONE))

        query_set = self.get_query_set(request, user_data_representation)
        context = dict()

        if self.time_type == user_models.DataRepresentation.TimeChoices.PERIOD:
            start = datetime.datetime.strptime(request.GET["time"], DATE_FORMAT)
            end = datetime.datetime.strptime(request.GET["end_time"], DATE_FORMAT)
            context["data"] = query_set.information_for_period(start, end)
        elif self.time_type == user_models.DataRepresentation.TimeChoices.TIME:
            time = datetime.datetime.strptime(request.GET["time"], DATE_FORMAT)
            context["data"] = query_set.information_for_time(time)
        else:
            context["data"] = query_set.information_for_time(now)

        return context

    @abstractmethod
    def get_query_set(self, request, user_data_representation):
        pass


class SingleLocationInformationView(LocationInformationView):
    location_manager: Manager = None  # TODO exception, if none in child class

    def get_query_set(self, request, user_data_representation):
        location_id = user_data_representation.location_id
        return self.location_manager.filter_for_id(location_id)


class HospitalInformationView(LocationInformationView):
    def get_query_set(self, request, user_data_representation):
        return hospital_models.Bed.hospital_objects.all()


class MultipleLocationsInformationView(LocationInformationView):
    location_manager: Manager = None  # TODO exception, if none in child class

    def get_query_set(self, request, user_data_representation):

        if self.location_type == user_models.DataRepresentation.LocationChoices.HOSPITAL:
            return self.location_manager.all()
        else:
            location_id = user_data_representation.location_id
            if self.location_type == user_models.DataRepresentation.LocationChoices.WARD:
                return self.location_manager.all_from_ward(location_id)
            elif self.location_type == user_models.DataRepresentation.LocationChoices.ROOM:
                return self.location_manager.all_from_room(location_id)


class LocationHistoryView(LocationDataResponseView, ABC):

    def get_context(self, request, user_data_representation: user_models.UserDataRepresentation):
        context = dict()
        start = user_data_representation.time
        end = user_data_representation.end_time

        query_set = self.get_query_set(request)

        for time in (start + ((end - start) / 9) * n for n in range(10)):
            context[time.strftime(DATE_FORMAT)] = query_set.occupancy_for_time(time)

        return {"data": context}

    @abstractmethod
    def get_query_set(self, request):
        pass


class SingleLocationHistoryView(LocationHistoryView):
    location_manager: Manager = None

    def get_query_set(self, request):
        return self.location_manager.filter_for_id(request.GET["location_id"])


class HospitalHistoryView(LocationHistoryView):
    def get_query_set(self, request):
        return hospital_models.Bed.hospital_objects.all()


class AllocationView(View):
    def get(self, request, location_type, theme_type, time_type):
        user_models.DataRepresentation.objects.get(location_type=location_type,
                                                   theme_type=theme_type,
                                                   time_type=time_type)

        if theme_type == user_models.DataRepresentation.ThemeChoices.INFORMATION:
            if location_type == user_models.DataRepresentation.LocationChoices.HOSPITAL:
                return HospitalInformationView.as_view(location_type=location_type, theme_type=theme_type,
                                                       time_type=time_type)(request)
            else:

                location_manager = None
                if location_type == user_models.DataRepresentation.LocationChoices.WARD:
                    location_manager = hospital_models.Ward.objects
                elif location_type == user_models.DataRepresentation.LocationChoices.ROOM:
                    location_manager = hospital_models.Room.objects

                return SingleLocationInformationView \
                    .as_view(location_type=location_type, theme_type=theme_type,
                             time_type=time_type, location_manager=location_manager)(request)
        elif theme_type == user_models.DataRepresentation.ThemeChoices.HISTORY:
            if location_type == user_models.DataRepresentation.LocationChoices.HOSPITAL:
                return HospitalHistoryView.as_view(location_type=location_type, theme_type=theme_type,
                                                   time_type=time_type)(request)
            else:
                location_manager = None  # TODO delete replicas
                if location_type == user_models.DataRepresentation.LocationChoices.WARD:
                    location_manager = hospital_models.Ward.objects
                elif location_type == user_models.DataRepresentation.LocationChoices.ROOM:
                    location_manager = hospital_models.Room.objects

                return SingleLocationHistoryView \
                    .as_view(location_type=location_type, theme_type=theme_type,
                             time_type=time_type, location_manager=location_manager)(request)
        else:
            location_manager = None  # TODO delete replicas
            if theme_type == user_models.DataRepresentation.ThemeChoices.ALL_WARDS:
                location_manager = hospital_models.Ward.objects
            elif theme_type == user_models.DataRepresentation.ThemeChoices.ALL_ROOMS:
                location_manager = hospital_models.Room.objects
            elif theme_type == user_models.DataRepresentation.ThemeChoices.ALL_BEDS:
                location_manager = hospital_models.Bed.objects

            return MultipleLocationsInformationView \
                .as_view(location_type=location_type, theme_type=theme_type,
                         time_type=time_type, location_manager=location_manager)(request)

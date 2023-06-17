import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View

import json

from dashboard.models.user_models.user_models import UserDataRepresentation, DataRepresentation, User
from dashboard.services.view_service import get_locations_for_time
from dashboard.utils import ModelJSONEncoder


class UpdateOrderView(View):
    def put(self, request):
        data = json.loads(request.body.decode("utf-8"))

        # update all
        for date in data:  # TODO check if its the right user
            UserDataRepresentation.objects.filter(id=int(date["id"])).update(order=int(date["order"]))
        return HttpResponse(status=200)


class DeleteUserDataRepresentation(View):
    def delete(self, request):
        data = json.loads(request.body.decode("utf-8"))
        UserDataRepresentation.objects.filter(id=int(data["id"])).delete()

        return HttpResponse(status=200)


class CreateUserDataRepresentationView(View):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        location_type = data["location_type"]
        theme_type = data["theme_type"]
        time_type = data["time_type"]

        data_representation = DataRepresentation.objects.get(location_type=location_type,
                                                             theme_type=theme_type,
                                                             time_type=time_type)
        user = User.objects.last()  # TODO change

        user_data_representation = UserDataRepresentation.objects.create_user_data_representation(data_representation,
                                                                                                  user)

        context = {
            "user_data_representation": user_data_representation,
            "data_representation": data_representation
        }

        locations = get_locations_for_time(user_data_representation, location_type, time_type,
                                           datetime.datetime.now(tz=ZoneInfo(settings.TIME_ZONE)))
        if locations:
            context["locations"] = locations

        return JsonResponse(context, encoder=ModelJSONEncoder)
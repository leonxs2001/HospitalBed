import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

import json

from dashboard.models import DataRepresentation, UserDataRepresentation
from dashboard.utils import ModelJSONEncoder


class ManageUserDataRepresentationView(View):

    @method_decorator(login_required)
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        location_type = data["location_type"]
        theme_type = data["theme_type"]
        time_type = data["time_type"]

        data_representation = DataRepresentation.objects.get(location_type=location_type,
                                                             theme_type=theme_type,
                                                             time_type=time_type)
        user = request.user

        user_data_representation = UserDataRepresentation.objects.create_user_data_representation(data_representation,
                                                                                                  user)
        context = {
            "user_data_representation": user_data_representation,
            "data_representation": data_representation
        }

        locations = user_data_representation.locations
        if locations:
            context["locations"] = locations

        return JsonResponse(context, encoder=ModelJSONEncoder)

    @method_decorator(login_required)
    def delete(self, request):
        data = json.loads(request.body.decode("utf-8"))
        UserDataRepresentation.objects.filter(id=int(data["id"]), user=request.user).delete()

        return HttpResponse(status=200)

    @method_decorator(login_required)
    def put(self, request):
        data = json.loads(request.body.decode("utf-8"))

        # update all
        for date in data:
            UserDataRepresentation.objects.filter(id=int(date["id"]), user=request.user).update(order=int(date["order"]))
        return HttpResponse(status=200)

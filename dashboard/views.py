import datetime
import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django.views.generic import TemplateView

from dashboard.models import DataRepresentation, User, UserDataRepresentation, Department, Ward, Room
from dashboard.services.view_service import get_locations_for_time
from dashboard.utils import ModelJSONEncoder


def create_data_representation(request):
    DataRepresentation.objects.create(location_type="H", theme_type="I", time_type="T")
    DataRepresentation.objects.create(location_type="H", theme_type="I", time_type="N")
    DataRepresentation.objects.create(location_type="H", theme_type="I", time_type="P")

    DataRepresentation.objects.create(location_type="D", theme_type="I", time_type="T")
    DataRepresentation.objects.create(location_type="D", theme_type="I", time_type="N")
    DataRepresentation.objects.create(location_type="D", theme_type="I", time_type="P")

    DataRepresentation.objects.create(location_type="W", theme_type="I", time_type="T")
    DataRepresentation.objects.create(location_type="W", theme_type="I", time_type="N")
    DataRepresentation.objects.create(location_type="W", theme_type="I", time_type="P")

    DataRepresentation.objects.create(location_type="R", theme_type="I", time_type="T")
    DataRepresentation.objects.create(location_type="R", theme_type="I", time_type="N")
    DataRepresentation.objects.create(location_type="R", theme_type="I", time_type="P")

    DataRepresentation.objects.create(location_type="H", theme_type="D", time_type="T")
    DataRepresentation.objects.create(location_type="H", theme_type="D", time_type="N")
    DataRepresentation.objects.create(location_type="H", theme_type="D", time_type="P")

    DataRepresentation.objects.create(location_type="H", theme_type="W", time_type="T")
    DataRepresentation.objects.create(location_type="H", theme_type="W", time_type="N")
    DataRepresentation.objects.create(location_type="H", theme_type="W", time_type="P")

    DataRepresentation.objects.create(location_type="H", theme_type="R", time_type="T")
    DataRepresentation.objects.create(location_type="H", theme_type="R", time_type="N")
    DataRepresentation.objects.create(location_type="H", theme_type="R", time_type="P")

    DataRepresentation.objects.create(location_type="H", theme_type="B", time_type="T")
    DataRepresentation.objects.create(location_type="H", theme_type="B", time_type="N")

    DataRepresentation.objects.create(location_type="D", theme_type="W", time_type="T")
    DataRepresentation.objects.create(location_type="D", theme_type="W", time_type="N")
    DataRepresentation.objects.create(location_type="D", theme_type="W", time_type="P")

    DataRepresentation.objects.create(location_type="D", theme_type="R", time_type="T")
    DataRepresentation.objects.create(location_type="D", theme_type="R", time_type="N")
    DataRepresentation.objects.create(location_type="D", theme_type="R", time_type="P")

    DataRepresentation.objects.create(location_type="D", theme_type="B", time_type="T")
    DataRepresentation.objects.create(location_type="D", theme_type="B", time_type="N")

    DataRepresentation.objects.create(location_type="W", theme_type="R", time_type="T")
    DataRepresentation.objects.create(location_type="W", theme_type="R", time_type="N")
    DataRepresentation.objects.create(location_type="W", theme_type="R", time_type="P")

    DataRepresentation.objects.create(location_type="W", theme_type="B", time_type="T")
    DataRepresentation.objects.create(location_type="W", theme_type="B", time_type="N")

    DataRepresentation.objects.create(location_type="R", theme_type="B", time_type="T")
    DataRepresentation.objects.create(location_type="R", theme_type="B", time_type="N")

    DataRepresentation.objects.create(location_type="H", theme_type="H", time_type="P")
    DataRepresentation.objects.create(location_type="D", theme_type="H", time_type="P")
    DataRepresentation.objects.create(location_type="W", theme_type="H", time_type="P")
    DataRepresentation.objects.create(location_type="R", theme_type="H", time_type="P")

    return HttpResponse("hjgk")


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        user = User.objects.all().first()
        context["user"] = user

        user_data_representations = UserDataRepresentation.objects.filter(user=user) \
            .select_related("data_representation")
        context["user_data_representations"] = user_data_representations

        context["departments"] = Department.objects.all()
        context["wards"] = Ward.objects.all()
        context["rooms"] = Room.objects.all()
        context["now"] = datetime.datetime.now(datetime.timezone.utc)

        context["structured_data_representations"] = DataRepresentation.objects.structured_data_representations()

        return context


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

        user_data_representation = UserDataRepresentation.objects.create_user(data_representation, user)

        context = {
            "user_data_representation": user_data_representation,
            "data_representation": data_representation
        }

        locations = get_locations_for_time(user_data_representation, location_type, time_type)
        if locations:
            context["locations"] = locations

        return JsonResponse(context, encoder=ModelJSONEncoder)

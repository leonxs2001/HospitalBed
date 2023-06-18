import datetime

from django.http import HttpResponse
from django.views.generic import TemplateView

from dashboard.models.user_models import user_models
from dashboard.models.hospital_models import hospital_models
from dashboard.services.hl7_services import parse_all_hl7_messages


def create_data_representation(request):
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="I", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="I", time_type="N")
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="I", time_type="P")

    user_models.DataRepresentation.objects.create(location_type="W", theme_type="I", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="W", theme_type="I", time_type="N")
    user_models.DataRepresentation.objects.create(location_type="W", theme_type="I", time_type="P")

    user_models.DataRepresentation.objects.create(location_type="R", theme_type="I", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="R", theme_type="I", time_type="N")
    user_models.DataRepresentation.objects.create(location_type="R", theme_type="I", time_type="P")

    user_models.DataRepresentation.objects.create(location_type="H", theme_type="W", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="W", time_type="N")
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="W", time_type="P")

    user_models.DataRepresentation.objects.create(location_type="H", theme_type="R", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="R", time_type="N")
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="R", time_type="P")

    user_models.DataRepresentation.objects.create(location_type="H", theme_type="B", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="H", theme_type="B", time_type="N")

    user_models.DataRepresentation.objects.create(location_type="W", theme_type="R", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="W", theme_type="R", time_type="N")
    user_models.DataRepresentation.objects.create(location_type="W", theme_type="R", time_type="P")

    user_models.DataRepresentation.objects.create(location_type="W", theme_type="B", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="W", theme_type="B", time_type="N")

    user_models.DataRepresentation.objects.create(location_type="R", theme_type="B", time_type="T")
    user_models.DataRepresentation.objects.create(location_type="R", theme_type="B", time_type="N")

    user_models.DataRepresentation.objects.create(location_type="H", theme_type="H", time_type="P")
    user_models.DataRepresentation.objects.create(location_type="W", theme_type="H", time_type="P")
    user_models.DataRepresentation.objects.create(location_type="R", theme_type="H", time_type="P")

    return HttpResponse("hjgk")


def parse_hl7(request):
    parse_all_hl7_messages()
    return HttpResponse()


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        user = user_models.User.objects.all().first()
        context["user"] = user

        user_data_representations = user_models.UserDataRepresentation.objects.filter(user=user) \
            .select_related("data_representation")
        context["user_data_representations"] = user_data_representations

        context["wards"] = hospital_models.Ward.objects.all()
        context["rooms"] = hospital_models.Room.objects.all()
        context["now"] = datetime.datetime.now(datetime.timezone.utc)

        context[
            "structured_data_representations"] = user_models.DataRepresentation.objects.structured_data_representations()

        return context

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

import json

from dashboard.models import DataRepresentation, UserDataRepresentation
from dashboard.utils import ModelJSONEncoder


class ManageUserDataRepresentationView(View):
    """View for the Management of the UserDatatRepresentation."""

    @method_decorator(login_required)
    def post(self, request):
        """
        Creates a new UserDataRepresentation from the given location_type,
        theme_type and time_type in the request body.
        """
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

        # give back the created UserDataRepresentation and its related DataRepresentation
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
        """Deletes a UserDataRepresentation from the given id in the request body."""

        data = json.loads(request.body.decode("utf-8"))

        # use the user in the filter for the deletion
        # so that a user can't delete a foreign UserDataRepresentation
        UserDataRepresentation.objects.filter(id=int(data["id"]), user=request.user).delete()

        return HttpResponse(status=200)

    @method_decorator(login_required)
    def put(self, request):
        """Updates UserDataRepresentations from the given order and id list in the request body."""
        data = json.loads(request.body.decode("utf-8"))

        # update all
        for date in data:
            # use the user in the filter for the Update
            # so that a user can't update a foreign UserDataRepresentation
            UserDataRepresentation.objects.filter(id=int(date["id"]), user=request.user).update(order=int(date["order"]))
        return HttpResponse(status=200)

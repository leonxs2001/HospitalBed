import json

from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from dashboard.models import hospital_models
from dashboard.models.user_models import Token, UserDataRepresentation, DataRepresentation
from dashboard.utils import ModelJSONEncoder, DATE_FORMAT
from dashboard.views.location_data_views import DataGeneratorFactory


def token_required(view_func):
    """Decorator for a view with a required authentication with a token."""

    def wrapper(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            token_obj = Token.objects.get(key=token)
            if token_obj.is_valid():
                # update the user datetime
                token_obj.used = timezone.now()
                token_obj.save()
                request.user = token_obj.user
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse("The token is not valid anymore.", status=401)
        except ObjectDoesNotExist:
            return HttpResponseForbidden("The token does not exist.")

    return wrapper


# TODO think about transmitted name convention
class TokenView(View):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))

        username = data["username"]
        password = data["password"]

        user = authenticate(username=username, password=password)

        if user:
            try:
                token = user.auth_token
                if not token.is_valid():
                    token.delete()
                    token = Token.objects.create(user=user)
            except ObjectDoesNotExist:
                token = Token.objects.create(user=user)

            return JsonResponse({
                "token": token.key,
                username: username
            }, encoder=ModelJSONEncoder)
        else:
            return HttpResponse("Incorrect username or password.", status=401)

    @method_decorator(token_required)
    def delete(self, request):
        token = request.user.auth_token

        if token.is_valid():
            token.delete()

        return HttpResponse(status=200)


class ManageUserDataRepresentationView(View):
    """View for the Management of the UserDatatRepresentation."""

    @method_decorator(token_required)
    def post(self, request):
        """
        Creates a new UserDataRepresentation from the given location_type,
        theme_type and time_type in the request body.
        """
        data = json.loads(request.body.decode("utf-8"))

        data_representation = DataRepresentation.objects.get(id=int(data["dataRepresentationId"]))
        user = request.user

        user_data_representation = UserDataRepresentation.objects.create_user_data_representation(data_representation,
                                                                                                  user)

        # give back the created UserDataRepresentation and its related DataRepresentation
        context = {
            "user_data_representation": user_data_representation,
        }

        return JsonResponse(context, encoder=ModelJSONEncoder)

    @method_decorator(token_required)
    def delete(self, request, user_data_representation_id):
        """Deletes a UserDataRepresentation from the given id."""

        # use the user in the filter for the deletion
        # so that a user can't delete a foreign UserDataRepresentation
        UserDataRepresentation.objects.filter(id=user_data_representation_id, user=request.user).delete()

        return HttpResponse(status=200)

    @method_decorator(token_required)
    def get(self, request, user_data_representation_id):
        """Returns the right data in a HttpResponse."""

        user_data_representation = UserDataRepresentation.objects.select_related('data_representation').get(
            id=user_data_representation_id)

        # get the DataGenerator strategy from the factory method
        data_generator = DataGeneratorFactory.create_data_generator(user_data_representation.data_representation)

        context = dict()
        manager = user_data_representation.data_representation.location_manager

        # generate the data for the context
        data = data_generator.generate_data(user_data_representation, manager)

        context["data"] = data  # todo change the structure (result in first place not hidden behind "data"
        return JsonResponse(context, ModelJSONEncoder)

    @method_decorator(token_required)
    def patch(self, request, user_data_representation_id):
        """Update the given attributes."""

        try:
            user_data_representation = UserDataRepresentation.objects.select_related('data_representation').get(
                id=user_data_representation_id)
        except ObjectDoesNotExist:
            return HttpResponse("The UserDataRepresentation does not exist.", status=404)

        data = json.loads(request.body.decode("utf-8"))
        location_type = user_data_representation.data_representation.location_type

        if "time" in data:
            user_data_representation.time = timezone.datetime.strptime(data["time"], DATE_FORMAT)

        if "endTime" in data:
            user_data_representation.end_time = timezone.datetime.strptime(data["endTime"], DATE_FORMAT)

        if "locationId" in data:
            location_id = data["locationId"]
            try:
                if location_type == DataRepresentation.LocationChoices.ROOM:
                    user_data_representation.room_id = location_id
                elif location_type == DataRepresentation.LocationChoices.WARD:
                    user_data_representation.ward_id = location_id
            except IntegrityError:
                return HttpResponse("The locationId is not an existing location.", status=422)

        user_data_representation.save()
        return HttpResponse(status=200)


class ManageUserDataRepresentationsView(View):
    @method_decorator(token_required)
    def patch(self, request):
        """Updates UserDataRepresentations from the given order and id list in the request body."""

        data = json.loads(request.body.decode("utf-8"))

        # update all
        for date in data:
            # use the user in the filter for the Update
            # so that a user can't update a foreign UserDataRepresentation
            UserDataRepresentation.objects.filter(id=int(date["id"]), user=request.user).update(
                order=int(date["order"]))
        return HttpResponse(status=200)


class DataRepresentationsView(View):
    @method_decorator(token_required)
    def get(self, request):
        context = [
            {
                "id": representation.id,
                "locationType": representation.get_location_type_display(),
                "themeType": representation.get_theme_type_display(),
                "timeType": representation.get_time_type_display(),
            }
            for representation in DataRepresentation.objects.all()
        ]
        return JsonResponse(context, ModelJSONEncoder, safe=False)

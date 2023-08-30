import datetime

from django.db import models
from django.utils import timezone

from dashboard.models import hospital_models
from dashboard.models import user_models


class UserManager(models.Manager):
    """The Manager for the User-model."""

    def get_by_natural_key(self, username):
        """Overrides the method of the framework to get the User by a given username."""

        return self.get(username=username)


class DataRepresentationManager(models.Manager):
    """The Manager for the DataRepresentationManager-model."""

    def structured_data_representations(self):
        """
        Returns all the data representations in a structured way.
        They are organised by the location_type and theme_type in a tree structure.
        The return value is a dictionary (with the location_type as key),
        containing dictionaries (with the theme_type as key),
        containing the set of belonging data_representations.
        """

        structured_result = dict()
        data_representations = self.all()

        # go through all data_representations
        for data_representation in data_representations:

            # get the existing location_dict from the structured_result or create it for the current location_type
            location_dict = dict()
            if data_representation.location_type in structured_result:
                location_dict = structured_result[data_representation.location_type]
            else:
                structured_result[data_representation.location_type] = location_dict

            # get the existing theme_set from the location_dict or create it for the current theme_type
            theme_set = set()
            if data_representation.theme_type in location_dict:
                theme_set = location_dict[data_representation.theme_type]
            else:
                location_dict[data_representation.theme_type] = theme_set

            # add the data_representation to the theme_set
            theme_set.add(data_representation)

        return structured_result


class UserDataRepresentationManager(models.Manager):
    """The Manager for the UserDataRepresentationManager-model."""

    def create_user_data_representation(self, data_representation, user):
        """Creates and returns a new UserDataRepresentation in the Database from a given DataRepresentation and user."""

        # get the time and end_time attribute based on the time_type
        time = None
        end_time = None
        if data_representation.time_type == user_models.DataRepresentation.TimeChoices.TIME:
            time = timezone.now()
        elif data_representation.time_type == user_models.DataRepresentation.TimeChoices.PERIOD:
            time = timezone.now() - datetime.timedelta(weeks=4)
            end_time = timezone.now()

        # get the right location based on the location_type
        ward = None
        room = None
        if data_representation.location_type == user_models.DataRepresentation.LocationChoices.WARD:
            ward = hospital_models.Ward.objects.first()
        elif data_representation.location_type == user_models.DataRepresentation.LocationChoices.ROOM:
            room = hospital_models.Room.objects.first()

        # get a new order based on the greatest used order from the user
        max_order = user_models.UserDataRepresentation.objects.filter(user=user).aggregate(max_order=models.Max('order'))['max_order']
        new_order = 0
        if max_order is not None:
            new_order = max_order + 1

        return self.create(time=time, end_time=end_time, order=new_order,
                           user=user, data_representation=data_representation,
                           ward=ward, room=room)

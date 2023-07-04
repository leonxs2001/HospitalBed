from django.contrib.auth.models import AbstractBaseUser
from django.db import models

from dashboard.models.hospital_models import hospital_models
from dashboard.models.user_models.user_managers import UserDataRepresentationManager, DataRepresentationManager, \
    UserManager
from dashboard.utils import DATE_FORMAT


class DataRepresentation(models.Model):
    objects = DataRepresentationManager()

    class LocationChoices(models.TextChoices):  # TODO namen dazu
        HOSPITAL = "H"
        WARD = "W"
        ROOM = "R"

    class ThemeChoices(models.TextChoices):
        INFORMATION = "I"
        ALL_BEDS = "B"
        ALL_ROOMS = "R"
        ALL_WARDS = "W"
        HISTORY = "H"

    class TimeChoices(models.TextChoices):
        NEARTIME = "N"
        TIME = "T"
        PERIOD = "P"

    location_type = models.CharField(max_length=1,
                                     choices=LocationChoices.choices,
                                     default=LocationChoices.HOSPITAL)
    theme_type = models.CharField(max_length=1,
                                  choices=ThemeChoices.choices,
                                  default=ThemeChoices.INFORMATION)
    time_type = models.CharField(max_length=1,
                                 choices=TimeChoices.choices,
                                 default=TimeChoices.TIME)

    class Meta:
        unique_together = ('location_type', 'theme_type', 'time_type')


class User(AbstractBaseUser):
    objects = UserManager()

    username = models.CharField(max_length=32, unique=True)

    data_representations = models.ManyToManyField(DataRepresentation, through="UserDataRepresentation")
    USERNAME_FIELD = "username"


class UserDataRepresentation(models.Model):
    objects = UserDataRepresentationManager()

    time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    order = models.IntegerField(default=0)

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    data_representation = models.ForeignKey(DataRepresentation, on_delete=models.PROTECT)
    ward = models.ForeignKey(hospital_models.Ward, on_delete=models.PROTECT, null=True)
    room = models.ForeignKey(hospital_models.Room, on_delete=models.PROTECT, null=True)

    class Meta:  # TODO maxbe indexing? und meta reinnhemn in uml
        ordering = ["order"]

    @property
    def formatted_time(self):
        if self.time:
            return self.time.strftime(DATE_FORMAT)
        return None

    @property
    def formatted_end_time(self):
        if self.end_time:
            return self.end_time.strftime(DATE_FORMAT)
        return None

    @property
    def location_id(self):
        if self.ward_id:
            return self.ward_id
        elif self.room_id:
            return self.room_id
        else:
            return None

from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone

from dashboard.models.hospital_models import Ward, Room
from dashboard.models.hospital_models import Bed
from dashboard.orm import DataRepresentationManager, UserManager, UserDataRepresentationManager
from dashboard.utils import DATE_FORMAT


class DataRepresentation(models.Model):
    objects = DataRepresentationManager()

    class LocationChoices(models.TextChoices):
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
    time_type = models.CharField(max_length=1, choices=TimeChoices.choices, default=TimeChoices.TIME)

    @property
    def location_manager(self):
        if self.theme_type == self.ThemeChoices.INFORMATION or \
                self.theme_type == DataRepresentation.ThemeChoices.HISTORY:
            if self.location_type == self.LocationChoices.WARD:
                return Ward.objects
            elif self.location_type == self.LocationChoices.ROOM:
                return Room.objects
            else:
                return Bed.hospital_objects
        else:
            if self.theme_type == self.ThemeChoices.ALL_WARDS:
                return Ward.objects
            elif self.theme_type == self.ThemeChoices.ALL_ROOMS:
                return Room.objects
            else:
                return Bed.objects

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
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT, null=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, null=True)

    class Meta:
        ordering = ["order"]

    @property
    def locations(self):
        now = timezone.now()
        if self.data_representation.location_type != DataRepresentation.LocationChoices.HOSPITAL:
            location_class = None
            if self.data_representation.location_type == DataRepresentation.LocationChoices.WARD:
                location_class = Ward
            elif self.data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
                location_class = Room

            if self.data_representation.time_type == DataRepresentation.TimeChoices.TIME:
                return location_class.objects.filter_for_time(self.time)
            elif self.data_representation.time_type == DataRepresentation.TimeChoices.PERIOD:
                return location_class.objects.filter_for_period(self.time, self.end_time)
            else:
                return location_class.objects.filter_for_time(now)
        else:
            return []

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

from abc import ABC, abstractmethod
import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import models
from django.db.models import QuerySet, Manager, Q, TextChoices, Aggregate, Max, F, Subquery


class TimeFilterQuerySetMixin(QuerySet, ABC):
    def filter_for_time(self, time: datetime):
        return self.filter(date_of_activation__lt=time, date_of_expiry__gt=time)

    def filter_for_period(self, start: datetime, end: datetime):
        self.filter(Q(date_of_activation__range=(start, end)) | Q(date_of_expiry__range=(start, end)))


class TimeAnnotationQuerySetMixin(TimeFilterQuerySetMixin, ABC):
    @abstractmethod
    def time_annotation(self, time: datetime.datetime):
        pass

    @abstractmethod
    def period_of_time_annotation(self, time: datetime.datetime):
        pass

    def for_time(self, time: datetime.datetime):
        return self.filter_for_time(time).time_annotation(time)

    def for_period_of_time(self, start: datetime.datetime, end: datetime.datetime):
        return self.filter_for_period(start, end).period_of_time_annotation(start, end)


class LocationOccupancyQuerySetMixin(QuerySet, ABC):
    def occupancy_annotation(self, time: datetime.datetime):
        pass  # TODO fill

    def occupancy_over_period_annotation(self, start: datetime, end: datetime):
        pass


class SexQuerySetMixin(QuerySet, ABC):
    def sex_annotation(self, time: datetime.datetime):
        pass  # TODO fill

    def sex_over_period_annotation(self, start: datetime.datetime, end: datetime.datetime):
        pass


class AgeQuerySetMixin(QuerySet, ABC):
    def average_age_annotation(self, time: datetime):
        pass  # TODO fill

    def average_age_over_period_annotation(self, start: datetime, end: datetime):
        pass  # TODO fill


class DepartmentQuerySet(LocationOccupancyQuerySetMixin, SexQuerySetMixin, TimeAnnotationQuerySetMixin):

    def time_annotation(self, time: datetime.datetime):
        pass  # TODO write

    def period_of_time_annotation(self, time: datetime.datetime):
        pass


class WardQuerySet(LocationOccupancyQuerySetMixin, SexQuerySetMixin, TimeAnnotationQuerySetMixin):

    def time_annotation(self, time: datetime.datetime):
        pass  # TODO write

    def period_of_time_annotation(self, time: datetime.datetime):
        pass


class RoomQuerySet(LocationOccupancyQuerySetMixin, SexQuerySetMixin, TimeAnnotationQuerySetMixin):

    def time_annotation(self, time: datetime.datetime):
        pass  # TODO write

    def period_of_time_annotation(self, time: datetime.datetime):
        pass


class BedQuerySet(QuerySet):
    def sex_and_age_annotation(self):
        pass  # fill

    def occupancy_and_sex_aggregation(self):
        pass

    def occupancy_and_sex_over_period_aggregation(self):
        pass


class DataRepresentationManager(Manager):
    def structured_data_representations(self):
        structured_result = dict()
        data_representations = self.all()

        for data_representation in data_representations:
            location_dict = dict()
            if data_representation.location_type in structured_result:
                location_dict = structured_result[data_representation.location_type]
            else:
                structured_result[data_representation.location_type] = location_dict

            theme_set = set()
            if data_representation.theme_type in location_dict:
                theme_set = location_dict[data_representation.theme_type]
            else:
                location_dict[data_representation.theme_type] = theme_set

            theme_set.add(data_representation)

        return structured_result


class UserDataRepresentationManager(Manager):
    def create_user(self, data_representation, user):
        time = None
        end_time = None
        department = None
        ward = None
        room = None

        if data_representation.time_type == DataRepresentation.TimeChoices.TIME:
            time = datetime.datetime.now()
        elif data_representation.time_type == DataRepresentation.TimeChoices.PERIOD:
            time = datetime.datetime.now() - datetime.timedelta(weeks=4)
            end_time = datetime.datetime.now(tz=ZoneInfo(settings.TIME_ZONE))

        if data_representation.location_type == DataRepresentation.LocationChoices.DEPARTMENT:
            department = Department.objects.first()
        elif data_representation.location_type == DataRepresentation.LocationChoices.WARD:
            ward = Ward.objects.first()
        elif data_representation.location_type == DataRepresentation.LocationChoices.ROOM:
            room = Room.objects.first()

        max_order = max_order = UserDataRepresentation.objects.aggregate(max_order=Max('order'))['max_order']

        return self.create(time=time, end_time=end_time, order=max_order + 1,
                           user=user, data_representation=data_representation,
                           ward=ward, department=department, room=room)


class Patient(models.Model):
    class SexChoices(models.TextChoices):
        MALE = "M", "Mann"
        FEMALE = "F", "Frau"
        DIVERSE = "D", "Divers"

    patient_id = models.IntegerField(primary_key=True)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=SexChoices.choices)


class Visit(models.Model):
    visit_id = models.IntegerField(primary_key=True)
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(null=True)

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)


class LocationMixin(models.Model):
    name = models.CharField(max_length=32)
    date_of_activation = models.DateTimeField()
    date_of_expiry = models.DateTimeField()

    class Meta:
        abstract = True

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._get_pk_val() == other._get_pk_val()


class Ward(LocationMixin):
    objects = WardQuerySet.as_manager()


class Department(LocationMixin):
    objects = DepartmentQuerySet.as_manager()
    wards = models.ManyToManyField(Ward)


class Room(LocationMixin):
    objects = RoomQuerySet.as_manager()
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT)


class Bed(LocationMixin):
    objects = BedQuerySet.as_manager()
    room = models.ForeignKey(Room, on_delete=models.PROTECT)


class Stay(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)
    movement_id = models.IntegerField()

    visit = models.ForeignKey(Visit, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT)
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT)
    room = models.ForeignKey(Room, on_delete=models.PROTECT)


class Discharge(models.Model):
    movement_id = models.IntegerField()

    stay = models.ForeignKey(Stay, on_delete=models.PROTECT)


class DataRepresentation(models.Model):
    objects = DataRepresentationManager()

    class LocationChoices(TextChoices):  # TODO namen dazu
        HOSPITAL = "H"
        DEPARTMENT = "D"
        WARD = "W"
        ROOM = "R"

    class ThemeChoices(TextChoices):
        INFORMATION = "I"
        ALL_BEDS = "B"
        ALL_ROOMS = "R"
        ALL_WARDS = "W"
        ALL_DEPARTMENTS = "D"
        HISTORY = "H"

    class TimeChoices(TextChoices):
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


class User(models.Model):
    name = models.CharField(max_length=32)

    data_representations = models.ManyToManyField(DataRepresentation, through="UserDataRepresentation")


class UserDataRepresentation(models.Model):
    objects = UserDataRepresentationManager()

    time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    order = models.IntegerField(default=0)

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    data_representation = models.ForeignKey(DataRepresentation, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, null=True)
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT, null=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, null=True)

    class Meta:  # TODO maxbe indexing? und meta reinnhemn in uml
        ordering = ["order"]

    @property
    def formatted_time(self):
        if self.time:
            return self.time.strftime("%Y-%m-%dT%H:%M")
        return None

    @property
    def formatted_end_time(self):
        if self.end_time:
            return self.end_time.strftime("%Y-%m-%dT%H:%M")
        return None

import datetime
from abc import ABC, abstractmethod

from django.db import models, IntegrityError
from django.db.models import functions


class SexAnnotationQuerySetMixin(models.QuerySet, ABC):
    number_of_men = models.Count("stay", distinct=True,
                                 filter=models.Q(stay__visit__patient__sex="M"))
    number_of_women = models.Count("stay", distinct=True,
                                   filter=models.Q(stay__visit__patient__sex="F"))
    number_of_diverse = models.Count("stay", distinct=True,
                                     filter=models.Q(
                                         stay__visit__patient__sex="D"))

    def sex_annotation(self):
        return self.annotate(number_of_diverse=self.number_of_diverse,
                             number_of_men=self.number_of_men,
                             number_of_women=self.number_of_women)

    def sex_over_period_annotation(self, start: datetime.datetime, end: datetime.datetime):
        pass  # TODO fill


class AgeAnnotationQuerySetMixin(models.QuerySet, ABC):
    def age_annotation(self):
        today = datetime.date.today()

        # Extract year, month, and day from the current date
        current_year = today.year
        current_month = today.month
        current_day = today.day

        age_in_years = current_year - models.F('stay__visit__patient__date_of_birth__year')

        average_age = models.Avg(age_in_years - functions.Cast(
            models.Q(stay__visit__patient__date_of_birth__month__lt=current_month) | models.Q(
                stay__visit__patient__date_of_birth__month__lt=current_month) & models.Q(
                stay__visit__patient__date_of_birth__day__lt=current_day),
            output_field=models.IntegerField()))

        return self.annotate(average_age=average_age)

    def average_age_over_period_annotation(self, start: datetime, end: datetime):
        pass  # TODO fill


class LocationFilterQuerySetMixin(models.QuerySet, ABC):
    def filter_for_id(self, ID: str):
        return self.filter(id=ID)

    def all(self):
        return super(LocationFilterQuerySetMixin, self).all()

    @abstractmethod
    def all_from_ward(self, ward_id: str):
        pass

    @abstractmethod
    def all_from_room(self, room_id: str):
        pass


class TimeQuerySetMixin(models.QuerySet, ABC):
    def filter_for_time(self, time: datetime):
        return self.filter(date_of_activation__lt=time, date_of_expiry__gt=time)

    def filter_for_period(self, start: datetime, end: datetime):
        return self.filter(
            models.Q(date_of_activation__range=(start, end)) | models.Q(date_of_expiry__range=(start, end)))


class LocationInformationQuerySetMixin(TimeQuerySetMixin, ABC):

    def information_for_time(self, time: datetime.datetime):
        return self.filter_for_time(time).get_information(time)

    def information_for_period(self, start: datetime.datetime, end: datetime.datetime):
        return self.filter_for_period(start, end).get_information_for_period(start, end)

    @abstractmethod
    def get_information(self, time: datetime.datetime):
        pass

    @abstractmethod
    def get_information_for_period(self, start: datetime, end: datetime):
        pass


class LocationOccupancyQuerySetMixin(TimeQuerySetMixin, ABC):

    def occupancy_for_time(self, time: datetime.datetime):
        return self.filter_for_time(time).get_occupancy(time)

    def occupancy_for_period(self, start: datetime.datetime, end: datetime.datetime):
        return self.filter_for_period(start, end).get_occupancy_for_period(start, end)

    @abstractmethod
    def get_occupancy(self, time: datetime.datetime):
        pass

    @abstractmethod
    def get_occupancy_for_period(self, start: datetime, end: datetime):
        pass


class WardQuerySet(LocationInformationQuerySetMixin, LocationOccupancyQuerySetMixin, LocationFilterQuerySetMixin,
                   SexAnnotationQuerySetMixin):

    def all_from_ward(self, ward_id: str):
        return self.filter_for_id(ward_id)

    def all_from_room(self, room_id: str):
        return self.filter(room__id=room_id)

    def get_information(self, time: datetime.datetime):
        return self.sex_annotation().get_occupancy(time)

    def get_information_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill

    def get_occupancy(self, time: datetime.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        max_number = models.Count("room__bed", distinct=True,
                                  filter=models.Q(room__bed__date_of_activation__lt=time,
                                                  room__bed__date_of_expiry__gt=time))

        return self.annotate(number=number, max_number=max_number).annotate(
            occupancy=functions.Round((models.F("number") / models.F("max_number")) * 100, 2))

    def get_occupancy_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill


class RoomQuerySet(LocationInformationQuerySetMixin, LocationOccupancyQuerySetMixin, LocationFilterQuerySetMixin,
                   SexAnnotationQuerySetMixin, AgeAnnotationQuerySetMixin):

    def all_from_ward(self, ward_id: str):
        return self.filter(ward__id=ward_id)

    def all_from_room(self, room_id: str):
        return self.filter_for_id(room_id)

    def get_information(self, time: datetime.datetime):
        return self.sex_annotation().age_annotation().get_occupancy(time)

    def get_information_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill

    def get_occupancy(self, time: datetime.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        max_number = models.Count("bed", distinct=True,
                                  filter=models.Q(bed__date_of_activation__lt=time,
                                                  bed__date_of_expiry__gt=time))

        return self.annotate(number=number, max_number=max_number).annotate(
            occupancy=functions.Round((models.F("number") / models.F("max_number")) * 100, 2))

    def get_occupancy_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill


class BedQuerySet(LocationInformationQuerySetMixin, LocationFilterQuerySetMixin, SexAnnotationQuerySetMixin,
                  AgeAnnotationQuerySetMixin):

    def all_from_ward(self, ward_id: str):
        return self.filter(room__ward__id=ward_id)

    def all_from_room(self, room_id: str):
        return self.filter(room__id=room_id)

    def get_information(self, time: datetime.datetime):
        return self.sex_annotation().age_annotation()

    def get_information_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill


class HospitalBedQuerySet(LocationInformationQuerySetMixin, LocationOccupancyQuerySetMixin):
    def all(self):
        return super(HospitalBedQuerySet, self).all()

    def get_information(self, time: datetime.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        max_number = models.Count("id")
        occupancy = functions.Round((number / max_number) * 100, 2)

        query_set = self.aggregate(number_of_diverse=SexAnnotationQuerySetMixin.number_of_diverse,
                                   number_of_men=SexAnnotationQuerySetMixin.number_of_men,
                                   number_of_women=SexAnnotationQuerySetMixin.number_of_women,
                                   number=number,
                                   max_number=max_number,
                                   occupancy=occupancy)

        return query_set

    def get_information_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill

    def get_occupancy(self, time: datetime.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        max_number = models.Count("id")
        occupancy = functions.Round((number / max_number) * 100, 2)

        query_set = self.aggregate(number=number,
                                   max_number=max_number,
                                   occupancy=occupancy)

        return query_set

    def get_occupancy_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill

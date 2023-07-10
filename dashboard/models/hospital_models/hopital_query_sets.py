import datetime
from abc import ABC, abstractmethod

from django.conf.global_settings import TIME_ZONE
from django.db import models, IntegrityError
from django.db.models import functions, expressions, aggregates
from django.utils import timezone

from dashboard.models.hospital_models import hospital_models


class SexAnnotationQuerySetMixin(models.QuerySet, ABC):

    def sex_annotation(self, time):
        stay_filter = models.Q(date_of_activation__lt=time) & (models.Q(date_of_expiry__isnull=True) | models.Q(date_of_expiry__gt=time))
        number_of_men = models.Count("stay", distinct=True,
                                     filter=models.Q(stay__visit__patient__sex="M") & stay_filter)
        number_of_women = models.Count("stay", distinct=True,
                                       filter=models.Q(stay__visit__patient__sex="F") & stay_filter)
        number_of_diverse = models.Count("stay", distinct=True,
                                         filter=models.Q(
                                             stay__visit__patient__sex="D") & stay_filter)
        return self.annotate(  # TODO hier auch
            number_of_diverse=number_of_diverse,
            number_of_men=number_of_men,
            number_of_women=number_of_women
        )

    def sex_over_period_annotation(self, start: timezone.datetime, end: timezone.datetime):
        micro_duration = (end - start).total_seconds() * 1000000
        micro_seconds = models.ExpressionWrapper(
            models.Case(
                expressions.When(models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=end),
                                 then=models.Value(end, output_field=models.DateTimeField())),
                default=models.F("stay__end_date")
            )
            -
            models.Case(
                expressions.When(stay__start_date__lt=start,
                                 then=models.Value(start, output_field=models.DateTimeField())),
                default=models.F("stay__start_date")
            ),
            output_field=models.BigIntegerField()
        )

        stay_period_filter = (models.Q(stay__end_date=None, stay__start_date__lt=end) |
                              models.Q(stay__start_date__range=(start, end)) |
                              models.Q(stay__end_date__range=(start, end)) |
                              models.Q(stay__start_date__lt=start, stay__end_date__gt=start) |
                              models.Q(stay__start_date__lt=end, stay__end_date__gt=end))

        return self.annotate(  # stay muss in dem bereich liegen also rein in filter
            number_of_men=models.Sum(
                models.Case(
                    models.When(models.Q(stay__visit__patient__sex="M") & stay_period_filter, then=micro_seconds),
                    default=models.Value(0)
                ),
            ) / micro_duration,
            number_of_women=models.Sum(
                models.Case(
                    models.When(models.Q(stay__visit__patient__sex="F") & stay_period_filter, then=micro_seconds),
                    default=models.Value(0)
                ),
            ) / micro_duration,
            number_of_diverse=models.Sum(
                models.Case(
                    models.When(models.Q(stay__visit__patient__sex="D") & stay_period_filter, then=micro_seconds),
                    default=models.Value(0)
                ),
            ) / micro_duration
        )


class AgeAnnotationQuerySetMixin(models.QuerySet, ABC):
    def age_annotation(self, time: datetime):
        # Extract year, month, and day from the current date
        current_year = time.year
        current_month = time.month
        current_day = time.day

        age_in_years = current_year - models.F('visit__patient__date_of_birth__year')

        average_age = hospital_models.Stay.objects.filter(
            models.Q(id__in=models.OuterRef("stay__id")) &
            models.Q(start_date__lt=time) & (models.Q(end_date__isnull=True) | models.Q(end_date__gt=time))
        ).annotate(
            age=age_in_years - functions.Cast(
                models.Q(visit__patient__date_of_birth__month__gt=current_month) | models.Q(
                    visit__patient__date_of_birth__month=current_month) & models.Q(
                    visit__patient__date_of_birth__day__gt=current_day),
                output_field=models.IntegerField()
            )
        ).annotate(average_age=models.Func(models.F("age"), function="Avg")).values("average_age")
        return self.annotate(average_age=models.Subquery(average_age)).exclude(average_age=None)

    def age_over_period_annotation(self, start: datetime, end: datetime):
        stay_period_filter = (models.Q(end_date=None, start_date__lt=end) |
                              models.Q(start_date__range=(start, end)) |
                              models.Q(end_date__range=(start, end)) |
                              models.Q(start_date__lt=start, end_date__gt=start) |
                              models.Q(start_date__lt=end, end_date__gt=end))

        average_age = hospital_models.Stay.objects.filter(
            id__in=models.OuterRef("stay__id")
        ).filter(stay_period_filter).alias(
            adjusted_start_date=models.Case(
                expressions.When(start_date__lt=start,
                                 then=models.Value(start, output_field=models.DateTimeField())),
                default=models.F("start_date")
            ),
            adjusted_end_date=models.Case(
                expressions.When(models.Q(end_date=None) | models.Q(end_date__gt=end),
                                 then=models.Value(end, output_field=models.DateTimeField())),
                default=models.F("end_date")
            ),
        ).alias(
            average_time=functions.Cast(
                models.F("adjusted_start_date") +
                models.ExpressionWrapper(
                    functions.Cast(
                        models.ExpressionWrapper(
                            models.F("adjusted_end_date") - models.F("adjusted_start_date"),
                            output_field=models.BigIntegerField()
                        ) / 2,
                        output_field=models.BigIntegerField()
                    ),
                    output_field=models.DurationField()
                ),
                output_field=models.DateTimeField()
            )
        ).annotate(
            age=models.F("average_time__year") - models.F("visit__patient__date_of_birth__year")
                - functions.Cast(
                models.Q(visit__patient__date_of_birth__month__gt=models.F("average_time__month")) | models.Q(
                    visit__patient__date_of_birth__month=models.F("average_time__month")) & models.Q(
                    visit__patient__date_of_birth__day__gt=models.F("average_time__day")),
                output_field=models.IntegerField()
            )

        ).annotate(
            average_age=models.Func(models.F("age"), function="Avg")
        ).values("average_age")

        return self.annotate(average_age=models.Subquery(average_age))


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

    def filter_for_period(self, start: datetime, end: datetime):  # TODO change
        return self.filter(
            models.Q(date_of_activation__range=(start, end)) |
            models.Q(date_of_expiry__range=(start, end)) |
            models.Q(date_of_activation__lt=start, date_of_expiry__gt=start) |
            models.Q(date_of_activation__lt=end, date_of_expiry__gt=end))


class LocationInformationQuerySetMixin(TimeQuerySetMixin, ABC):

    def information_for_time(self, time: timezone.datetime):
        return self.filter_for_time(time).get_information(time)

    def information_for_period(self, start: timezone.datetime, end: timezone.datetime):
        return self.filter_for_period(start, end).get_information_for_period(start, end)

    @abstractmethod
    def get_information(self, time: timezone.datetime):
        pass

    @abstractmethod
    def get_information_for_period(self, start: datetime, end: datetime):
        pass


class LocationOccupancyQuerySetMixin(TimeQuerySetMixin, ABC):

    def occupancy_for_time(self, time: timezone.datetime):
        return self.filter_for_time(time).get_occupancy(time)

    @abstractmethod
    def get_occupancy(self, time: timezone.datetime):
        pass


class WardQuerySet(LocationInformationQuerySetMixin, LocationOccupancyQuerySetMixin, LocationFilterQuerySetMixin,
                   SexAnnotationQuerySetMixin):

    def all_from_ward(self, ward_id: str):
        return self.filter_for_id(ward_id)

    def all_from_room(self, room_id: str):
        return self.filter(room__id=room_id)

    def get_information(self, time: timezone.datetime):
        return self.sex_annotation(time).annotate(
            max_number=models.Count("room__bed", distinct=True,
                                    filter=models.Q(room__bed__date_of_activation__lt=time,
                                                    room__bed__date_of_expiry__gt=time)),
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse")
        )

    def get_information_for_period(self, start: datetime, end: datetime):
        bed_count = hospital_models.Bed.objects.filter(
            models.Q(room__ward__id=expressions.OuterRef("id")) &
            (
                    models.Q(date_of_activation__range=(start, end)) |
                    models.Q(date_of_expiry__range=(start, end)) |
                    models.Q(date_of_activation__lt=start, date_of_expiry__gt=start) |
                    models.Q(date_of_activation__lt=end, date_of_expiry__gt=end)
            )
        ).annotate(count=expressions.Func(models.F("id"), function="Count")).values("count")

        return self.sex_over_period_annotation(start, end).annotate(
            max_number=models.Subquery(bed_count),
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse")
        )

    def get_occupancy(self, time: timezone.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        max_number = models.Count("room__bed", distinct=True,
                                  filter=models.Q(room__bed__date_of_activation__lt=time,
                                                  room__bed__date_of_expiry__gt=time))

        return self.annotate(number=number, max_number=max_number)


class RoomQuerySet(LocationInformationQuerySetMixin, LocationOccupancyQuerySetMixin, LocationFilterQuerySetMixin,
                   SexAnnotationQuerySetMixin, AgeAnnotationQuerySetMixin):

    def all_from_ward(self, ward_id: str):
        return self.filter(ward__id=ward_id)

    def all_from_room(self, room_id: str):
        return self.filter_for_id(room_id)

    def get_information(self, time: timezone.datetime):
        return self.sex_annotation(time).age_annotation(time).annotate(
            max_number=models.Count("bed", distinct=True,
                                    filter=models.Q(bed__date_of_activation__lt=time,
                                                    bed__date_of_expiry__gt=time)),
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse")
        )

    def get_information_for_period(self, start: datetime, end: datetime):
        bed_count = hospital_models.Bed.objects.filter(
            models.Q(room__id=expressions.OuterRef("id")) &
            (
                    models.Q(date_of_activation__range=(start, end)) |
                    models.Q(date_of_expiry__range=(start, end)) |
                    models.Q(date_of_activation__lt=start, date_of_expiry__gt=start) |
                    models.Q(date_of_activation__lt=end, date_of_expiry__gt=end)
            )
        ).annotate(count=expressions.Func(models.F("id"), function="Count")).values("count")

        return self.age_over_period_annotation(start, end).sex_over_period_annotation(start, end).annotate(
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse"),
            max_number=models.Subquery(bed_count)
        )

    def get_occupancy(self, time: timezone.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        max_number = models.Count("bed", distinct=True,
                                  filter=models.Q(bed__date_of_activation__lt=time,
                                                  bed__date_of_expiry__gt=time))

        return self.annotate(number=number, max_number=max_number)


class BedQuerySet(LocationInformationQuerySetMixin, LocationFilterQuerySetMixin, SexAnnotationQuerySetMixin,
                  AgeAnnotationQuerySetMixin):

    def all_from_ward(self, ward_id: str):
        return self.filter(room__ward__id=ward_id)

    def all_from_room(self, room_id: str):
        return self.filter(room__id=room_id)

    def get_information(self, time: timezone.datetime):
        return self.sex_annotation(time).age_annotation(time)

    def get_information_for_period(self, start: datetime, end: datetime):
        return self.sex_over_period_annotation(start, end).age_over_period_annotation(start, end)


class HospitalBedQuerySet(LocationInformationQuerySetMixin, LocationOccupancyQuerySetMixin, SexAnnotationQuerySetMixin):
    def all(self):
        return super(HospitalBedQuerySet, self).all()

    def get_information(self, time: timezone.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        query_set = self.sex_annotation(time)
        test = [e for e in query_set]


        return query_set.aggregate(number_of_diverse=models.Sum("number_of_diverse"),
                                         number_of_men=models.Sum("number_of_men"),
                                         number_of_women=models.Sum("number_of_women"),
                                         number=number,
                                         max_number=models.Count("id", distinct=True))

    def get_information_for_period(self, start: datetime, end: datetime):
        pass  # TODO fill

    def get_occupancy(self, time: timezone.datetime):
        number = models.Count('stay', distinct=True,
                              filter=models.Q(stay__start_date__lt=time) & (
                                      models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time)))
        max_number = models.Count("id", distinct=True)
        occupancy = functions.Round((number / max_number) * 100, 2)

        query_set = self.aggregate(number=number,
                                   max_number=max_number,
                                   occupancy=occupancy)

        return query_set

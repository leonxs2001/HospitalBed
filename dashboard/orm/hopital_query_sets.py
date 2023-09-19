import datetime
from abc import ABC, abstractmethod

from django.db import models
from django.db.models import functions, expressions
from django.utils import timezone

from dashboard.models import hospital_models


class SexAnnotationQuerySet(models.QuerySet):
    """QuerySet for the annotation of sex to the locations."""

    def sex_annotation(self, time: datetime.datetime):
        """Returns the given QuerySet with the annotated number of persons per sex for a given time."""

        # create the reusable time filter for all different sexes
        stay_time_filter = models.Q(date_of_activation__lt=time) & (
                models.Q(date_of_expiry__isnull=True) | models.Q(date_of_expiry__gt=time))

        # create the annotations for the different sexes by counting the number of people with this sex
        number_of_men = models.Count("stay", distinct=True,
                                     filter=models.Q(
                                         stay__visit__patient__sex=hospital_models.Patient.SexChoices.MALE) & stay_time_filter)
        number_of_women = models.Count("stay", distinct=True,
                                       filter=models.Q(
                                           stay__visit__patient__sex=hospital_models.Patient.SexChoices.FEMALE) & stay_time_filter)
        number_of_diverse = models.Count("stay", distinct=True,
                                         filter=models.Q(
                                             stay__visit__patient__sex=hospital_models.Patient.SexChoices.DIVERSE) & stay_time_filter)
        return self.annotate(
            number_of_diverse=number_of_diverse,
            number_of_men=number_of_men,
            number_of_women=number_of_women
        )

    def sex_over_period_annotation(self, start: datetime.datetime, end: datetime.datetime):
        """Returns the given QuerySet with the annotated number of persons per sex for a given period of time."""

        # create the annotation for the period of time in microseconds,
        # where the stay is inside the given period of time
        micro_seconds = models.ExpressionWrapper(
            # define the borders of the period of time based on the end_date and start_date
            # and subtract them to get the period of time
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

        # create the reusable period of time filter for all different sexes
        stay_period_filter = (models.Q(stay__end_date=None, stay__start_date__lt=end) |
                              models.Q(stay__start_date__range=(start, end)) |
                              models.Q(stay__end_date__range=(start, end)) |
                              models.Q(stay__start_date__lt=start, stay__end_date__gt=start) |
                              models.Q(stay__start_date__lt=end, stay__end_date__gt=end))

        return self.alias(
            # define an alias for the sum of the periods of time (in microseconds) of all stays
            # at the locations for all different sexes
            number_of_men_micros=models.Sum(
                models.Case(
                    models.When(models.Q(
                        stay__visit__patient__sex=hospital_models.Patient.SexChoices.MALE) & stay_period_filter,
                                then=micro_seconds),
                    default=models.Value(0)
                ),
            ),
            number_of_women_micros=models.Sum(
                models.Case(
                    models.When(models.Q(
                        stay__visit__patient__sex=hospital_models.Patient.SexChoices.FEMALE) & stay_period_filter,
                                then=micro_seconds),
                    default=models.Value(0)
                ),
            ),
            number_of_diverse_micros=models.Sum(
                models.Case(
                    models.When(models.Q(
                        stay__visit__patient__sex=hospital_models.Patient.SexChoices.DIVERSE) & stay_period_filter,
                                then=micro_seconds),
                    default=models.Value(0)
                ),
            ),

            # define an alias for the total periods of time (in microseconds)
            # by sum up the periods of time of all sexes
            total_micros=models.F("number_of_men_micros") +
                         models.F("number_of_women_micros") +
                         models.F("number_of_diverse_micros")

        ).annotate(
            # annotate the number of all sexes at the locations
            # by dividing the gender microseconds by the total microseconds
            number_of_men=functions.Coalesce(
                models.F("number_of_men_micros") / models.F("total_micros"),
                0
            ),
            number_of_women=functions.Coalesce(
                models.F("number_of_women_micros") / models.F("total_micros"),
                0
            ),
            number_of_diverse=functions.Coalesce(
                models.F("number_of_diverse_micros") / models.F("total_micros"),
                0
            ),
        )


class AgeAnnotationQuerySet(models.QuerySet):
    """QuerySet for the annotation of the average age to the locations."""

    def age_annotation(self, time: datetime.datetime):
        """Returns the given QuerySet with the average age for a given time."""

        # create the average age subquery for every location and the given time
        average_age = hospital_models.Stay.objects.filter(
            # filter the stays for the given time
            models.Q(id__in=models.OuterRef("stay__id")) &
            models.Q(start_date__lt=time) & (models.Q(end_date__isnull=True) | models.Q(end_date__gt=time))
        ).annotate(
            # annotate the age of every stay
            # The age is calculated from the difference between the years
            # and whether the birthday has already taken place or not
            age=time.year - models.F('visit__patient__date_of_birth__year') - functions.Cast(
                models.Q(visit__patient__date_of_birth__month__gt=time.month) | models.Q(
                    visit__patient__date_of_birth__month=time.month) & models.Q(
                    visit__patient__date_of_birth__day__gt=time.day),
                output_field=models.IntegerField()
            )
        ).annotate(
            # annotate the average of all the previous calculated ages of the location
            average_age=models.Func(models.F("age"), function="Avg")
        ).values("average_age")

        return self.annotate(average_age=models.Subquery(average_age)).distinct()

    def age_over_period_annotation(self, start: datetime.datetime, end: datetime.datetime):
        """Returns the given QuerySet with the annotated average age for a given period of time."""

        # create the average age subquery for every location and the given period of time
        average_age = hospital_models.Stay.objects.filter(
            id__in=models.OuterRef("stay__id")
        ).filter(
            # filter for the given period of time
            models.Q(end_date=None, start_date__lt=end) |
            models.Q(start_date__range=(start, end)) |
            models.Q(end_date__range=(start, end)) |
            models.Q(start_date__lt=start, end_date__gt=start) |
            models.Q(start_date__lt=end, end_date__gt=end)
        ).alias(
            # define the borders of the period of time based on the end_date and start_date as alias
            adjusted_start_date=models.Case(
                expressions.When(start_date__lt=start,
                                 then=models.Value(start, output_field=models.DateTimeField())),
                default=models.F("start_date")
            ),
            adjusted_end_date=models.Case(
                expressions.When(models.Q(end_date=None) | models.Q(end_date__gt=end),
                                 then=models.Value(end, output_field=models.DateTimeField())),
                default=models.F("end_date")
            )
        ).alias(
            # define an alias for the time between the defined borders
            average_time=functions.Cast(
                models.F("adjusted_start_date") +
                models.ExpressionWrapper(
                    functions.Cast(
                        models.ExpressionWrapper(
                            models.F("adjusted_start_date") - models.F("adjusted_end_date"),
                            output_field=models.BigIntegerField()
                        ) / 2,
                        output_field=models.BigIntegerField()
                    ),
                    output_field=models.DurationField()
                ),
                output_field=models.DateTimeField()
            ),
        ).annotate(
            # annotate the age of every stay
            # The age is calculated from the difference between the years
            # and whether the birthday has already taken place or not
            age=models.F("average_time__year") - models.F("visit__patient__date_of_birth__year")
                - functions.Cast(
                models.Q(visit__patient__date_of_birth__month__gt=models.F("average_time__month")) | models.Q(
                    visit__patient__date_of_birth__month=models.F("average_time__month")) & models.Q(
                    visit__patient__date_of_birth__day__gt=models.F("average_time__day")),
                output_field=models.IntegerField()
            ),
            # define the period of time (in microseconds) between the defined borders
            micro_seconds=models.ExpressionWrapper(
                models.F("adjusted_end_date") - models.F("adjusted_start_date"),
                output_field=models.BigIntegerField()
            )

        ).annotate(
            # annotate the average of all the previous calculated ages
            # by multiplying the sum of  the ages multiplied by the microseconds between the defined borders
            # and divide the result by the sum of all microseconds between the defined borders
            average_age=(
                            models.Func(models.F("age") * models.F("micro_seconds"), function="Sum")
                        ) / models.Func(models.F("micro_seconds"), function="Sum")
        ).values("average_age")

        return self.annotate(average_age=models.Subquery(average_age))


class LocationFilterQuerySet(models.QuerySet, ABC):
    """QuerySet for filtering the locations by specific attributes."""

    def filter_for_id(self, ID: str):
        """Returns the given QuerySet filtered by a given id."""

        return self.filter(id=ID)

    @abstractmethod
    def all_from_ward(self, ward_id: str):
        """Returns the given QuerySet filtered by a given ward_id."""
        pass

    @abstractmethod
    def all_from_room(self, room_id: str):
        """Returns the given QuerySet filtered by a given room_id."""
        pass


class TimeQuerySet(models.QuerySet, ABC):
    """QuerySet for filtering the locations by times or periods of times."""

    def filter_for_time(self, time: datetime.datetime):
        """Returns the given QuerySet filtered by a time."""

        return self.filter(date_of_activation__lt=time, date_of_expiry__gt=time)

    def filter_for_period(self, start: datetime, end: datetime):
        """Returns the given QuerySet filtered by a period of time."""

        return self.filter(
            models.Q(date_of_activation__range=(start, end)) |
            models.Q(date_of_expiry__range=(start, end)) |
            models.Q(date_of_activation__lt=start, date_of_expiry__gt=start) |
            models.Q(date_of_activation__lt=end, date_of_expiry__gt=end)
        )


class LocationInformationQuerySet(TimeQuerySet, ABC):
    """QuerySet for annotating the right information to the locations."""

    def information_for_time(self, time: timezone.datetime):
        """
        Returns the given QuerySet with the locations filtered by a given time
        and the right annotated information.
        """

        return self.filter_for_time(time).get_information(time)

    def information_for_period(self, start: timezone.datetime, end: timezone.datetime):
        """
        Returns the given QuerySet with the locations filtered by a given period of time
        and the right annotated information.
        """

        return self.filter_for_period(start, end).get_information_for_period(start, end)

    @abstractmethod
    def get_information(self, time: timezone.datetime):
        """Returns the given QuerySet with the right annotated information for a given time."""
        pass

    @abstractmethod
    def get_information_for_period(self, start: datetime, end: datetime):
        """Returns the given QuerySet with the right annotated information for a given period of time."""
        pass


class LocationOccupancyQuerySet(TimeQuerySet, ABC):
    """QuerySet for annotating the occupancy to the locations."""

    def occupancy(self, time: timezone.datetime):
        """
        Returns the given QuerySet with the locations filtered by a given time
        and the annotated occupancy.
        """
        return self.filter_for_time(time).get_occupancy(time)

    @abstractmethod
    def get_occupancy(self, time: timezone.datetime):
        """Returns the given QuerySet with the annotated occupancy for a given time."""
        pass


class WardQuerySet(LocationInformationQuerySet, LocationOccupancyQuerySet, LocationFilterQuerySet,
                   SexAnnotationQuerySet):
    """QuerySet for the Ward-model."""

    def all_from_ward(self, ward_id: str):
        return self.filter_for_id(ward_id)

    def all_from_room(self, room_id: str):
        return self.filter(room__id=room_id)

    def get_information(self, time: timezone.datetime):
        return self.sex_annotation(time).annotate(
            # annotate the max number of beds by counting them
            max_number=models.Count("room__bed", distinct=True,
                                    filter=models.Q(room__bed__date_of_activation__lt=time,
                                                    room__bed__date_of_expiry__gt=time)),
            # annotate the number of occupied beds by sum up the number of people of all sexes
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse")
        )

    def get_information_for_period(self, start: datetime, end: datetime):
        # create the subquery for the max number of beds
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
            # annotate the number of occupied beds by sum up the number of people of all sexes
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse")
        )

    def get_occupancy(self, time: timezone.datetime):
        return self.annotate(
            # annotate the number of occupied beds by counting the connected stays
            number=models.Count('stay', distinct=True,
                                filter=models.Q(stay__start_date__lt=time) & (
                                        models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time))),
            # annotate the max number of beds by counting them
            max_number=models.Count("room__bed", distinct=True,
                                    filter=models.Q(room__bed__date_of_activation__lt=time,
                                                    room__bed__date_of_expiry__gt=time))
        )


class RoomQuerySet(LocationInformationQuerySet, LocationOccupancyQuerySet, LocationFilterQuerySet,
                   SexAnnotationQuerySet, AgeAnnotationQuerySet):
    """QuerySet for the Room-model."""

    def all_from_ward(self, ward_id: str):
        return self.filter(ward__id=ward_id)

    def all_from_room(self, room_id: str):
        return self.filter_for_id(room_id)

    def get_information(self, time: timezone.datetime):
        return self.sex_annotation(time).age_annotation(time).annotate(
            # annotate the max number of beds by counting them
            max_number=models.Count("bed", distinct=True,
                                    filter=models.Q(bed__date_of_activation__lt=time,
                                                    bed__date_of_expiry__gt=time)),
            # annotate the number of occupied beds by sum up the number of people of all sexes
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse")
        )

    def get_information_for_period(self, start: datetime, end: datetime):
        # create the subquery for the max number of beds
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
            # annotate the number of occupied beds by sum up the number of people of all sexes
            number=models.F("number_of_men") + models.F("number_of_women") + models.F("number_of_diverse"),
            max_number=models.Subquery(bed_count)
        )

    def get_occupancy(self, time: timezone.datetime):
        return self.annotate(
            # annotate the number of occupied beds by counting the connected stays
            number=models.Count('stay', distinct=True,
                                filter=models.Q(stay__start_date__lt=time) & (
                                        models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time))),
            # annotate the max number of beds by counting them
            max_number=models.Count("bed", distinct=True,
                                    filter=models.Q(bed__date_of_activation__lt=time,
                                                    bed__date_of_expiry__gt=time))
        )


class BedQuerySet(LocationInformationQuerySet, LocationFilterQuerySet, SexAnnotationQuerySet,
                  AgeAnnotationQuerySet):
    """QuerySet for the Bed-model."""

    def all_from_ward(self, ward_id: str):
        return self.filter(room__ward__id=ward_id)

    def all_from_room(self, room_id: str):
        return self.filter(room__id=room_id)

    def get_information(self, time: timezone.datetime):
        return self.sex_annotation(time).age_annotation(time)

    def get_information_for_period(self, start: datetime, end: datetime):
        return self.sex_over_period_annotation(start, end).age_over_period_annotation(start, end)


class HospitalBedQuerySet(LocationInformationQuerySet, LocationOccupancyQuerySet, SexAnnotationQuerySet):
    """QuerySet for the Ward-model. Used to generate the information for a whole hospital."""

    def get_information(self, time: timezone.datetime):
        query_set = self.sex_annotation(time)

        return query_set.aggregate(
            # aggregate the number of the people with the different sexes from the beds
            number_of_diverse=models.Sum("number_of_diverse"),
            number_of_men=models.Sum("number_of_men"),
            number_of_women=models.Sum("number_of_women"),

            # annotate the number of occupied beds by counting the connected stays
            number=models.Count('stay', distinct=True,
                                filter=models.Q(stay__start_date__lt=time) & (
                                        models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time))),
            # annotate the max number of beds by counting them
            max_number=models.Count("id", distinct=True)
        )

    def get_information_for_period(self, start: datetime, end: datetime):
        # create the subquery for the max number of beds
        stay_period_filter = (models.Q(stay__end_date=None, stay__start_date__lt=end) |
                              models.Q(stay__start_date__range=(start, end)) |
                              models.Q(stay__end_date__range=(start, end)) |
                              models.Q(stay__start_date__lt=start, stay__end_date__gt=start) |
                              models.Q(stay__start_date__lt=end, stay__end_date__gt=end))

        query_set = self.sex_over_period_annotation(start, end)

        return query_set.aggregate(
            # aggregate the number of the people with the different sexes from the beds
            number_of_diverse=models.Sum("number_of_diverse"),
            number_of_men=models.Sum("number_of_men"),
            number_of_women=models.Sum("number_of_women"),

            # annotate the number of occupied beds by counting the connected stays
            number=models.Count('stay', distinct=True, filter=stay_period_filter),
            # annotate the max number of beds by counting them
            max_number=models.Count("id", distinct=True)
        )

    def get_occupancy(self, time: timezone.datetime):

        return self.aggregate(
            # annotate the number of occupied beds by counting the connected stays
            number=models.Count('stay', distinct=True,
                                filter=models.Q(stay__start_date__lt=time) & (
                                        models.Q(stay__end_date=None) | models.Q(stay__end_date__gt=time))),
            # annotate the max number of beds by counting them
            max_number=models.Count("id", distinct=True)
        )

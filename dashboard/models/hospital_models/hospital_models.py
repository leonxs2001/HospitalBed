from django.db import models

from dashboard.models.hospital_models import hopital_query_sets


class Patient(models.Model):
    class SexChoices(models.TextChoices):
        MALE = "M", "Mann"
        FEMALE = "F", "Frau"
        DIVERSE = "D", "Divers"

    patient_id = models.BigIntegerField(primary_key=True)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=SexChoices.choices)


class Visit(models.Model):
    visit_id = models.BigIntegerField(primary_key=True)
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(null=True)

    patient = models.ForeignKey(Patient, models.CASCADE)


class LocationMixin(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=32)
    date_of_activation = models.DateTimeField()
    date_of_expiry = models.DateTimeField()

    class Meta:
        abstract = True

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._get_pk_val() == other._get_pk_val()


class Ward(LocationMixin):
    objects = hopital_query_sets.WardQuerySet.as_manager()


class Room(LocationMixin):
    objects = hopital_query_sets.RoomQuerySet.as_manager()
    ward = models.ForeignKey(Ward,models.CASCADE)


class Bed(LocationMixin):
    objects = hopital_query_sets.BedQuerySet.as_manager()
    hospital_objects = hopital_query_sets.HospitalBedQuerySet.as_manager()
    room = models.ForeignKey(Room,models.CASCADE)


class Stay(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)
    movement_id = models.IntegerField()

    visit = models.ForeignKey(Visit,models.CASCADE)
    bed = models.ForeignKey(Bed,models.CASCADE)
    ward = models.ForeignKey(Ward,models.CASCADE)
    room = models.ForeignKey(Room,models.CASCADE)


class Discharge(models.Model):
    movement_id = models.IntegerField()

    stay = models.ForeignKey(Stay,models.CASCADE)

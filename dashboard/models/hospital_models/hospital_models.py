from django.db import models

from dashboard.models.hospital_models.hopital_query_sets import WardQuerySet, DepartmentQuerySet, RoomQuerySet, \
    BedQuerySet, HospitalBedQuerySet


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
    hospital_objects = HospitalBedQuerySet.as_manager()
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

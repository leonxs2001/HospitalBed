from django.db import models


# Create your models here.
class Patient(models.Model):
    patient_id = models.IntegerField(primary_key=True)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=8)


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


class Ward(LocationMixin):
    pass


class Department(LocationMixin):
    wards = models.ManyToManyField(Ward)


class Room(LocationMixin):
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT)


class Bed(LocationMixin):
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

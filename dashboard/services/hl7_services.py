import bisect
import os
import uuid
from abc import ABC, abstractmethod

import hl7
import datetime

# from dashboard.models import Patient
from django.db.models import QuerySet
from django.utils import timezone

from dashboard.models.hospital_models import hospital_models
from django.conf import settings

HL7_DATE_FORMAT = "%Y%m%d"
HL7_DATE_TIME_FORMAT = "%Y%m%d%H%M%S"

MSH_MESSAGE_CREATION_FIELD = 7
MSH_MESSAGE_TYPE_FIELD = 9
MESSAGE_TYPE_TYPE_COMPONENT = 1
MESSAGE_TYPE_TRIGGER_EVENT_COMPONENT = 2

PID_PATIENT_ID_FIELD = 2
PID_DOB_FIELD = 7
PID_SEX_FILED = 8

PV1_VISIT_ID_FIELD = 19
PV1_ADMISSION_DATE_FIELD = 44
PV1_DISCHARGE_DATE_FIELD = 45
PV1_PATIENT_LOCATION_FIELD = 3
PATIENT_LOCATION_WARD_COMPONENT = 1
PATIENT_LOCATION_ROOM_COMPONENT = 2
PATIENT_LOCATION_BED_COMPONENT = 3

ZBE_MOVEMENT_ID_FIELD = 1
ZBE_START_DATE_FIELD = 2


class Hl7Message(ABC):
    def __init__(self, message: hl7.Message):
        self._msh_segment = message.segment("MSH")
        self._pv1_segment = message.segment("PV1")
        self._pid_segment = message.segment("PID")
        self._zbe_segment = message.segment("ZBE")
        self.message_creation = self._msh_segment[MSH_MESSAGE_CREATION_FIELD]

    def _get_or_create_patient(self):
        patient_id_string = self._pid_segment.extract_field(field_num=PID_PATIENT_ID_FIELD)
        patient_id = int(patient_id_string)

        date_of_birth_string = self._pid_segment.extract_field(field_num=PID_DOB_FIELD)
        date_of_birth = timezone.datetime.strptime(date_of_birth_string, HL7_DATE_FORMAT).date()

        sex = self._pid_segment.extract_field(field_num=PID_SEX_FILED)

        return hospital_models.Patient.objects.get_or_create(patient_id=patient_id,
                                                             defaults={"date_of_birth": date_of_birth,
                                                                       "sex": sex})[0]

    def _get_or_create_visit(self, patient: hospital_models.Patient):
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        admission_date_string = self._pv1_segment.extract_field(
            field_num=PV1_ADMISSION_DATE_FIELD)  # is this right, if the patient was not in ward before
        admission_date = timezone.datetime.strptime(admission_date_string, HL7_DATE_TIME_FORMAT)

        return hospital_models.Visit.objects.get_or_create(visit_id=visit_id,
                                                           defaults={"admission_date": admission_date,
                                                                     "patient": patient})[0]

    def _get_or_create_ward(self):
        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        ward_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                  component_num=PATIENT_LOCATION_WARD_COMPONENT)

        return hospital_models.Ward.objects.get_or_create(id=ward_id,
                                                          defaults={"name": ward_id,
                                                                    "date_of_activation": start_date,
                                                                    "date_of_expiry": start_date + datetime.timedelta(
                                                                        weeks=1)})[0]

    def _get_or_create_room(self, ward: hospital_models.Ward):
        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        room_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                  component_num=PATIENT_LOCATION_ROOM_COMPONENT)

        return hospital_models.Room.objects.get_or_create(id=room_id, ward=ward,
                                                          defaults={"name": room_id,
                                                                    "date_of_activation": start_date,
                                                                    "date_of_expiry": start_date + datetime.timedelta(
                                                                        weeks=1)})[0]

    def _get_or_create_bed(self, room: hospital_models.Room):
        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        bed_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                 component_num=PATIENT_LOCATION_BED_COMPONENT)

        return hospital_models.Bed.objects.get_or_create(id=bed_id, room=room,
                                                         defaults={"name": bed_id,
                                                                   "date_of_activation": start_date,
                                                                   "date_of_expiry": start_date + datetime.timedelta(
                                                                       weeks=1)})[0]

    def _create_stay(self, visit: hospital_models.Visit):
        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)

        ward = self._get_or_create_ward()
        room = self._get_or_create_room(ward)
        bed = self._get_or_create_bed(room)

        return hospital_models.Stay.objects.create(movement_id=movement_id, start_date=start_date, visit=visit,
                                                   bed=bed, room=room, ward=ward)

    @abstractmethod
    def parse_message(self):
        pass


class AdmissionHl7Message(Hl7Message):
    def parse_message(self):
        # only parse the visit, if there is a given bed id
        bed_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                 component_num=PATIENT_LOCATION_BED_COMPONENT)
        if bed_id:
            patient = self._get_or_create_patient()
            visit = self._get_or_create_visit(patient)

            self._create_stay(visit)


class TransferHl7Message(Hl7Message):
    def parse_message(self):
        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)

        patient = self._get_or_create_patient()
        visit = self._get_or_create_visit(patient)

        # get last stay with visit and end_date == None
        stay = hospital_models.Stay.objects.filter(visit=visit, end_date=None).last()
        # set end date if stay is not none
        # could be None if the parsing starts after the admission
        if stay:
            stay.end_date = start_date
            stay.save()

        # only create the new stay, if there is a given bed id
        bed_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                 component_num=PATIENT_LOCATION_BED_COMPONENT)
        if bed_id:
            self._create_stay(visit)


class DischargeHl7Message(Hl7Message):
    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        discharge_date_string = self._pv1_segment.extract_field(field_num=PV1_DISCHARGE_DATE_FIELD)
        discharge_date = timezone.datetime.strptime(discharge_date_string, HL7_DATE_TIME_FORMAT)

        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)

        # update the visit discharge_date
        hospital_models.Visit.objects.filter(visit_id=visit_id).update(discharge_date=discharge_date)

        # get last stay with visit and end_date == None
        stay = hospital_models.Stay.objects.filter(visit_id=visit_id, end_date=None).last()

        # create discharge and save the new end_date if stay is not none
        if stay:
            hospital_models.Discharge.objects.create(movement_id=movement_id, stay=stay)

            stay.end_date = start_date
            stay.save()


class UpdateHl7Message(Hl7Message):
    def parse_message(self):
        patient_id_string = self._pid_segment.extract_field(field_num=PID_PATIENT_ID_FIELD)
        patient_id = int(patient_id_string)

        date_of_birth_string = self._pid_segment.extract_field(field_num=PID_DOB_FIELD)
        date_of_birth = timezone.datetime.strptime(date_of_birth_string, HL7_DATE_FORMAT).date()

        sex = self._pid_segment.extract_field(field_num=PID_SEX_FILED)

        hospital_models.Patient.objects.filter(patient_id=patient_id).update(sex=sex, date_of_birth=date_of_birth)


class CancelAdmissionHl7Message(Hl7Message):
    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        # get and delete the canceled stay if exists
        stay = hospital_models.Stay.objects.filter(visit_id=visit_id, movement_id=movement_id).last()
        if stay:
            stay.delete()


class CancelTransferHl7Message(Hl7Message):
    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        # get and delete the canceled stay if exists
        canceled_stay = hospital_models.Stay.objects.filter(visit_id=visit_id, movement_id=movement_id).last()
        if canceled_stay:
            canceled_stay.delete()

            # get the stay before and set the end date to None if exists
            old_stay = hospital_models.Stay.objects.filter(visit_id=visit_id, movement_id__lt=movement_id).last()
            if old_stay:
                old_stay.update(end_date=None)


class CancelDischargeHl7Message(Hl7Message):
    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        # get and delete discharge if exists
        discharge = hospital_models.Discharge.objects.select_related("stay").filter(movement_id=movement_id,
                                                                                    stay__visit_id=visit_id).last()
        if discharge:
            discharge.stay.end_date = None
            discharge.stay.save()
            discharge.delete()


class Hl7MessageParser:
    @classmethod
    def parse_hl7_message_from_directory(cls, path: str):
        # get all hl7 messages from the hl7_files
        hl7_messages = []
        for filename in os.listdir(path):
            if filename.endswith(".hl7"):
                file_path = os.path.join(path, filename)

                new_hl7_messages = cls._create_hl7_messages_from_file(file_path)
                # insert to the right position in the list (sorted)
                for new_hl7_message in new_hl7_messages:
                    bisect.insort(hl7_messages, new_hl7_message,
                                  key=lambda msg: msg.message_creation)

                os.remove(file_path)

        for hl7_message in hl7_messages:
            hl7_message.parse_message()

    @classmethod
    def _create_hl7_messages_from_file(cls, path: str) -> list:
        hl7_messages = []
        with open(path, "r", encoding="ISO-8859-1") as hl7_file:
            # read the string from the file
            hl7_messages_string = hl7_file.read()

            # wrong delimiter in hl7_files
            hl7_messages_string = hl7_messages_string.replace('\n', '\r')

            hl7_message_strings = hl7.split_file(hl7_messages_string)

            for hl7_message_string in hl7_message_strings:
                hl7_message = cls._create_hl7_message_from_string(hl7_message_string)
                if hl7_message:
                    hl7_messages.append(hl7_message)

        return hl7_messages

    @classmethod
    def _create_hl7_message_from_string(cls, message: str) -> Hl7Message:
        hl7_message = hl7.parse(message)
        message_type = hl7_message.segment("MSH").extract_field(field_num=MSH_MESSAGE_TYPE_FIELD,
                                                                component_num=MESSAGE_TYPE_TYPE_COMPONENT)
        trigger_event = hl7_message.segment("MSH").extract_field(field_num=MSH_MESSAGE_TYPE_FIELD,
                                                                 component_num=MESSAGE_TYPE_TRIGGER_EVENT_COMPONENT)
        if message_type == "ADT":
            if trigger_event == "A01":
                return AdmissionHl7Message(hl7_message)
            elif trigger_event == "A02":
                return TransferHl7Message(hl7_message)
            elif trigger_event == "A03" or trigger_event == "A07":
                return DischargeHl7Message(hl7_message)
            elif trigger_event == "A08":
                visit_id_string = hl7_message.segment("PV1").extract_field(field_num=PV1_VISIT_ID_FIELD)
                visit_id = int(visit_id_string)
                # handle like a transfer if there are only closed stays
                if not hospital_models.Stay.objects.filter(visit_id=visit_id, end_date=None).exists():
                    return TransferHl7Message(hl7_message)

                return UpdateHl7Message(hl7_message)
            elif trigger_event == "A11":
                return CancelAdmissionHl7Message(hl7_message)
            elif trigger_event == "A12":
                return CancelTransferHl7Message(hl7_message)
            elif trigger_event == "A13":
                return CancelDischargeHl7Message(hl7_message)

        return None

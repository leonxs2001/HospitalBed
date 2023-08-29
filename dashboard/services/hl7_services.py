import bisect
import os

from abc import ABC, abstractmethod

import hl7
import datetime

from django.utils import timezone

from dashboard.models import Patient, Visit, Ward, Room
from dashboard.models.hospital_models import Bed, Stay, Discharge

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
    """A Class for HL7-messages."""

    def __init__(self, message: hl7.Message):
        # extract all important segments and add them as instance attributes
        self._msh_segment = message.segment("MSH")
        self._pv1_segment = message.segment("PV1")
        self._pid_segment = message.segment("PID")
        self._zbe_segment = message.segment("ZBE")

        # extract the message creation attribute and add it as instance attribute
        self.message_creation = self._msh_segment[MSH_MESSAGE_CREATION_FIELD]

    def _get_or_create_patient(self):
        """Gets or creates a new patient from the message segments and return the result."""

        patient_id_string = self._pid_segment.extract_field(field_num=PID_PATIENT_ID_FIELD)
        patient_id = int(patient_id_string)

        date_of_birth_string = self._pid_segment.extract_field(field_num=PID_DOB_FIELD)
        date_of_birth = timezone.datetime.strptime(date_of_birth_string, HL7_DATE_FORMAT).date()

        sex = self._pid_segment.extract_field(field_num=PID_SEX_FILED)

        return Patient.objects.get_or_create(patient_id=patient_id,
                                             defaults={"date_of_birth": date_of_birth,
                                                       "sex": sex})[0]

    def _get_or_create_visit(self, patient: Patient):
        """Gets or creates a new visit from the message segments for a given patient and return the result."""

        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        admission_date_string = self._pv1_segment.extract_field(field_num=PV1_ADMISSION_DATE_FIELD)
        admission_date = timezone.datetime.strptime(admission_date_string, HL7_DATE_TIME_FORMAT)

        return Visit.objects.get_or_create(visit_id=visit_id,
                                           defaults={"admission_date": admission_date,
                                                     "patient": patient})[0]

    def _create_stay(self, visit: Visit):
        """Gets or creates a new stay from the message segments for a given visit and return the result."""

        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)

        ward = self.__get_or_create_ward()
        room = self.__get_or_create_room(ward)
        bed = self.__get_or_create_bed(room)

        return Stay.objects.create(movement_id=movement_id, start_date=start_date, visit=visit,
                                   bed=bed, room=room, ward=ward)

    def __get_or_create_ward(self):
        """Gets or creates a new ward from the message segments and return the result."""

        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        ward_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                  component_num=PATIENT_LOCATION_WARD_COMPONENT)

        return Ward.objects.get_or_create(id=ward_id,
                                          defaults={"name": ward_id,
                                                    "date_of_activation": start_date,
                                                    "date_of_expiry": start_date + datetime.timedelta(
                                                        weeks=1)})[0]

    def __get_or_create_room(self, ward: Ward):
        """Gets or creates a new room from the message segments for a given ward and return the result."""

        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        room_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                  component_num=PATIENT_LOCATION_ROOM_COMPONENT)

        return Room.objects.get_or_create(id=room_id, ward=ward,
                                          defaults={"name": room_id,
                                                    "date_of_activation": start_date,
                                                    "date_of_expiry": start_date + datetime.timedelta(
                                                        weeks=1)})[0]

    def __get_or_create_bed(self, room: Room):
        """Gets or creates a new bed from the message segments for a given room and return the result."""

        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)
        bed_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                 component_num=PATIENT_LOCATION_BED_COMPONENT)

        return Bed.objects.get_or_create(id=bed_id, room=room,
                                         defaults={"name": bed_id,
                                                   "date_of_activation": start_date,
                                                   "date_of_expiry": start_date + datetime.timedelta(
                                                       weeks=1)})[0]

    @abstractmethod
    def parse_message(self):
        """Parses the message from the segments in the instance attributes and saves the result in the database."""
        pass


class AdmissionHl7Message(Hl7Message):
    """A class for admission HL7-messages."""

    def parse_message(self):
        # only parse the visit, if there is a given bed id
        bed_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                 component_num=PATIENT_LOCATION_BED_COMPONENT)
        if bed_id:
            patient = self._get_or_create_patient()
            visit = self._get_or_create_visit(patient)

            self._create_stay(visit)


class TransferHl7Message(Hl7Message):
    """A class for transfer HL7-messages."""

    def parse_message(self):
        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)

        patient = self._get_or_create_patient()
        visit = self._get_or_create_visit(patient)

        # get the last stay with visit and end_date == None
        stay = Stay.objects.filter(visit=visit, end_date=None).last()
        # set end_date if stay is not none
        # the stay could be None if the parsing starts after the admission
        if stay:
            stay.end_date = start_date
            stay.save()

        # only create the new stay, if there is a given bed id
        bed_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                 component_num=PATIENT_LOCATION_BED_COMPONENT)
        if bed_id:
            self._create_stay(visit)


class DischargeHl7Message(Hl7Message):
    """A class for discharge HL7-messages."""

    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        discharge_date_string = self._pv1_segment.extract_field(field_num=PV1_DISCHARGE_DATE_FIELD)

        discharge_date = timezone.datetime.strptime(discharge_date_string, HL7_DATE_TIME_FORMAT)

        start_date_string = self._zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = timezone.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)

        # update the visits discharge_date
        Visit.objects.filter(visit_id=visit_id).update(discharge_date=discharge_date)

        # get the last stay with visit and end_date == None
        stay = Stay.objects.filter(visit_id=visit_id, end_date=None).last()

        # create the new discharge, set the end_date of the stay and safe the stay if the stay is not none
        if stay:
            Discharge.objects.create(movement_id=movement_id, stay=stay)

            stay.end_date = start_date
            stay.save()


class UpdateHl7Message(Hl7Message):
    """A class for update HL7-messages."""

    def parse_message(self):
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        # handle message also like a transfer and create a new stay if there are no open stays
        # there could be no open stays if the parsing starts after the admission
        if not Stay.objects.filter(visit_id=visit_id, end_date=None).exists():
            patient = self._get_or_create_patient()
            visit = self._get_or_create_visit(patient)
            # only create the new stay, if there is a given bed id
            bed_id = self._pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                                     component_num=PATIENT_LOCATION_BED_COMPONENT)
            if bed_id:
                self._create_stay(visit)

        # update the important patient attributes
        patient_id_string = self._pid_segment.extract_field(field_num=PID_PATIENT_ID_FIELD)
        patient_id = int(patient_id_string)

        date_of_birth_string = self._pid_segment.extract_field(field_num=PID_DOB_FIELD)
        date_of_birth = timezone.datetime.strptime(date_of_birth_string, HL7_DATE_FORMAT).date()

        sex = self._pid_segment.extract_field(field_num=PID_SEX_FILED)

        Patient.objects.filter(patient_id=patient_id).update(sex=sex, date_of_birth=date_of_birth)


class CancelAdmissionHl7Message(Hl7Message):
    """A class for the admission canceling HL7-messages."""

    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        # get and delete the canceled stay if it exists
        # couldn't exist if the parsing starts after the admission
        stay = Stay.objects.filter(visit_id=visit_id, movement_id=movement_id).last()
        if stay:
            stay.delete()


class CancelTransferHl7Message(Hl7Message):
    """A class for the transfer canceling HL7-messages."""
    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        # get and delete the canceled stay if exists
        # couldn't exist if the parsing starts after the admission
        canceled_stay = Stay.objects.filter(visit_id=visit_id, movement_id=movement_id).last()
        if canceled_stay:
            canceled_stay.delete()

            # reset the end_date of the old_stay to None if exists
            # couldn't exist if the parsing starts after the admission
            old_stay = Stay.objects.filter(visit_id=visit_id, movement_id__lt=movement_id).last()
            if old_stay:
                Stay.objects.filter(id=old_stay.id).update(end_date=None)


class CancelDischargeHl7Message(Hl7Message):
    """A class for the discharge canceling HL7-messages."""

    def parse_message(self):
        movement_id_string = self._zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
        movement_id = int(movement_id_string)
        visit_id_string = self._pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
        visit_id = int(visit_id_string)

        # get and delete discharge and update the end_date of the connected stay
        # and the discharge_date of the connected visit to None if exists
        # couldn't exist if the parsing starts after the admission
        discharge = Discharge.objects.select_related("stay__visit").filter(movement_id=movement_id,
                                                                           stay__visit_id=visit_id).last()
        if discharge:
            discharge.stay.end_date = None
            discharge.stay.save()
            discharge.stay.visit.discharge_date = None
            discharge.stay.visit.save()
            discharge.delete()


class Hl7MessageParser:
    """A class for the parsing of HL7-files."""

    @classmethod
    def parse_hl7_messages_from_directory(cls, path: str):
        """Parses all HL7-files in a given directory and save the results in the database."""

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
        # parse all messages in the sorted list
        for hl7_message in hl7_messages:
            hl7_message.parse_message()

    @classmethod
    def _create_hl7_messages_from_file(cls, path: str):
        """Parses a HL7-file on a given path into a list of Hl7Message instances."""

        hl7_messages = []
        with open(path, "r", encoding="ISO-8859-1") as hl7_file:
            # read the string from the file
            hl7_messages_string = hl7_file.read()

            # replace the wrong delimiters in the message string
            hl7_messages_string = hl7_messages_string.replace('\n', '\r')

            hl7_message_strings = hl7.split_file(hl7_messages_string)

            # go through the message strings from the file,
            # create the right Hl7Message instance and add it to the result list
            for hl7_message_string in hl7_message_strings:
                hl7_message = cls._create_hl7_message_from_string(hl7_message_string)
                if hl7_message:
                    hl7_messages.append(hl7_message)

        return hl7_messages

    @classmethod
    def _create_hl7_message_from_string(cls, message: str) -> Hl7Message:
        """Parses a given HL7-message string a Hl7Message instance return this instance."""
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
                return UpdateHl7Message(hl7_message)
            elif trigger_event == "A11":
                return CancelAdmissionHl7Message(hl7_message)
            elif trigger_event == "A12":
                return CancelTransferHl7Message(hl7_message)
            elif trigger_event == "A13":
                return CancelDischargeHl7Message(hl7_message)

        return None

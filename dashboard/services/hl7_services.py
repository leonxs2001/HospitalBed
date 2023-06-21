import bisect
import os
import uuid

import hl7
import datetime

# from dashboard.models import Patient
from django.db.models import QuerySet

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


def parse_all_hl7_messages():
    # get all hl7 messages from the hl7_files
    hl7_messages = []
    for filename in os.listdir(settings.HL7_DIRECTORY):
        if filename.endswith(".hl7"):
            new_hl7_messages = get_hl7_message_from_file(filename)
            # insert to the right position in the list (sorted)
            for new_hl7_message in new_hl7_messages:
                bisect.insort(hl7_messages, new_hl7_message,
                              key=lambda msg: msg.segment("MSH")[MSH_MESSAGE_CREATION_FIELD])

    for hl7_message in hl7_messages:
        parse_hl7_message(hl7_message)


def get_hl7_message_from_file(filename: str):
    hl7_messages = []
    with open(settings.HL7_DIRECTORY + "/" + filename, "r", encoding="ISO-8859-1") as hl7_file:
        # read the string from the file
        hl7_messages_string = hl7_file.read()

        # \r ein Segment wird von einem anderen Segment getrennt TODO change!!! überhaupt wichtig???
        hl7_messages_string = hl7_messages_string.replace('\n', '\r')

        hl7_message_strings = hl7.split_file(hl7_messages_string)

        for hl7_message_string in hl7_message_strings:
            hl7_message = hl7.parse(hl7_message_string)
            hl7_messages.append(hl7_message)

    return hl7_messages


def parse_hl7_message(hl7_message: hl7.Message):
    try:
        msh_segment = hl7_message.segment("MSH")
        pid_segment = hl7_message.segment("PID")
        pv1_segment = hl7_message.segment("PV1")
        zbe_segment = hl7_message.segment("ZBE")
    except KeyError:
        print("Klappt hier nicht")  # TODO anders händeln

    message_type = msh_segment.extract_field(field_num=MSH_MESSAGE_TYPE_FIELD,
                                             component_num=MESSAGE_TYPE_TYPE_COMPONENT)
    trigger_event = msh_segment.extract_field(field_num=MSH_MESSAGE_TYPE_FIELD,
                                              component_num=MESSAGE_TYPE_TRIGGER_EVENT_COMPONENT)

    if message_type == "ADT":
        if trigger_event == "A01":
            parse_new_visit(pid_segment, pv1_segment, zbe_segment)
        elif trigger_event == "A02":
            parse_transfer(pv1_segment, pid_segment, zbe_segment)
        elif trigger_event == "A03" or trigger_event == "A07":
            parse_discharge(pv1_segment, zbe_segment)
        elif trigger_event == "A08":
            parse_update_patient(pv1_segment, pid_segment, zbe_segment)
        elif trigger_event == "A11":
            parse_cancel_admit(pv1_segment, zbe_segment)
        elif trigger_event == "A12":
            parse_cancel_admit(pv1_segment, zbe_segment)
        elif trigger_event == "A13":
            parse_cancel_discharge(pv1_segment, zbe_segment)
        elif trigger_event == "A40":
            pass


def parse_cancel_discharge(pv1_segment: hl7.Segment, zbe_segment: hl7.Segment):
    movement_id_string = zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
    movement_id = int(movement_id_string)
    visit_id_string = pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
    visit_id = int(visit_id_string)

    # TODO angucken select_related --> keine doppelte abfrage
    # get and delete discharge if exists
    discharge = hospital_models.Discharge.objects.filter(movement_id=movement_id, stay__visit_id=visit_id).last()
    if discharge:
        discharge.stay.end_date = None
        discharge.stay.save()
        discharge.delete()


def parse_cancel_transfer(pv1_segment: hl7.Segment, zbe_segment: hl7.Segment):
    movement_id_string = zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
    movement_id = int(movement_id_string)
    visit_id_string = pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
    visit_id = int(visit_id_string)

    # get and delete the canceled stay if exists
    canceled_stay = hospital_models.Stay.objects.filter(visit_id=visit_id, movement_id=movement_id).last()
    if canceled_stay:
        canceled_stay.delete()

        # get the stay before and set the end date to None if exists
        old_stay = hospital_models.Stay.objects.filter(visit_id=visit_id, movement_id__lt=movement_id).last()
        if old_stay:
            old_stay.update(end_date=None)


def parse_cancel_admit(pv1_segment: hl7.Segment, zbe_segment: hl7.Segment):
    movement_id_string = zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
    movement_id = int(movement_id_string)
    visit_id_string = pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
    visit_id = int(visit_id_string)

    # get and delete the canceled stay if exists
    stay = hospital_models.Stay.objects.filter(visit_id=visit_id, movement_id=movement_id).last()
    if stay:
        stay.delete()


def parse_update_patient(pv1_segment: hl7.Segment, pid_segment: hl7.Segment, zbe_segment: hl7.Segment):
    patient_id_string = pid_segment.extract_field(field_num=PID_PATIENT_ID_FIELD)
    patient_id = int(patient_id_string)

    date_of_birth_string = pid_segment.extract_field(field_num=PID_DOB_FIELD)
    date_of_birth = datetime.datetime.strptime(date_of_birth_string, HL7_DATE_FORMAT).date()

    sex = pid_segment.extract_field(field_num=PID_SEX_FILED)

    hospital_models.Patient.objects.filter(id=patient_id).update(sex=sex, date_of_birth=date_of_birth)

    visit_id_string = pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
    visit_id = int(visit_id_string)

    # handle like a transfer if there are only closed stays
    if not hospital_models.Stay.objects.filter(visit_id=visit_id, end_date=None).exists():
        parse_transfer(pv1_segment, pid_segment, zbe_segment)


def parse_transfer(pv1_segment: hl7.Segment, pid_segment: hl7.Segment, zbe_segment: hl7.Segment):
    start_date_string = zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
    start_date = datetime.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)

    patient = get_or_create_patient(pid_segment)
    visit = get_or_create_visit(pv1_segment, patient)

    # get last stay with visit and end_date == None
    stay = hospital_models.Stay.objects.filter(visit=visit, end_date=None).last()
    # set end date if stay is not none
    # could be None if the parsing starts after the admission
    if stay:
        stay.end_date = start_date  # TODO sollte das nicht lieber end of movement sein????? Ist das richtig???
        stay.save()

    # only create the new stay, if there is a given bed id
    bed_id = pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                       component_num=PATIENT_LOCATION_BED_COMPONENT)
    if bed_id:
        create_stay(pv1_segment, zbe_segment, visit, start_date)


def parse_discharge(pv1_segment: hl7.Segment, zbe_segment: hl7.Segment):
    movement_id_string = zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
    movement_id = int(movement_id_string)
    visit_id_string = pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
    visit_id = int(visit_id_string)

    discharge_date_string = pv1_segment.extract_field(field_num=PV1_DISCHARGE_DATE_FIELD)
    discharge_date = datetime.datetime.strptime(discharge_date_string, HL7_DATE_TIME_FORMAT)

    start_date_string = zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
    start_date = datetime.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)

    # update the visit discharge_date
    hospital_models.Visit.objects.filter(visit_id=visit_id).update(discharge_date=discharge_date)

    # get last stay with visit and end_date == None
    stay = hospital_models.Stay.objects.filter(visit_id=visit_id, end_date=None).last()

    # create discharge and save the new end_date if stay is not none
    if stay:
        hospital_models.Discharge.objects.create(movement_id=movement_id, stay=stay)

        stay.end_date = start_date  # TODO sollte das nicht lieber end of movement sein????? Ist das richtig???
        stay.save()


def parse_new_visit(pid_segment: hl7.Segment, pv1_segment: hl7.Segment, zbe_segment: hl7.Segment):
    # only parse the visit, if there is a given bed id
    bed_id = pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                       component_num=PATIENT_LOCATION_BED_COMPONENT)
    if bed_id:
        start_date_string = zbe_segment.extract_field(field_num=ZBE_START_DATE_FIELD)
        start_date = datetime.datetime.strptime(start_date_string, HL7_DATE_TIME_FORMAT)

        patient = get_or_create_patient(pid_segment)
        visit = get_or_create_visit(pv1_segment, patient)

        create_stay(pv1_segment, zbe_segment, visit, start_date)


def get_or_create_patient(pid_segment: hl7.Segment):
    patient_id_string = pid_segment.extract_field(field_num=PID_PATIENT_ID_FIELD)
    patient_id = int(patient_id_string)

    date_of_birth_string = pid_segment.extract_field(field_num=PID_DOB_FIELD)
    date_of_birth = datetime.datetime.strptime(date_of_birth_string, HL7_DATE_FORMAT).date()

    sex = pid_segment.extract_field(field_num=PID_SEX_FILED)

    return hospital_models.Patient.objects.get_or_create(patient_id=patient_id,
                                                         defaults={"date_of_birth": date_of_birth,
                                                                   "sex": sex})[0]


def get_or_create_visit(pv1_segment: hl7.Segment, patient: hospital_models.Patient):
    visit_id_string = pv1_segment.extract_field(field_num=PV1_VISIT_ID_FIELD)
    visit_id = int(visit_id_string)

    admission_date_string = pv1_segment.extract_field(
        field_num=PV1_ADMISSION_DATE_FIELD)  # is this right, if the patient was not in ward before
    admission_date = datetime.datetime.strptime(admission_date_string, HL7_DATE_TIME_FORMAT)

    return hospital_models.Visit.objects.get_or_create(visit_id=visit_id,
                                                       defaults={"admission_date": admission_date,
                                                                 "patient": patient})[0]


def get_or_create_ward(pv1_segment: hl7.Segment,
                       start_date: datetime.datetime):
    ward_id = pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                        component_num=PATIENT_LOCATION_WARD_COMPONENT)

    return hospital_models.Ward.objects.get_or_create(id=ward_id,
                                                      defaults={"name": ward_id,
                                                                "date_of_activation": start_date,
                                                                "date_of_expiry": start_date + datetime.timedelta(
                                                                    weeks=1)})[0]


def get_or_create_room(pv1_segment: hl7.Segment, ward: hospital_models.Ward,
                       start_date: datetime.datetime):
    room_id = pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                        component_num=PATIENT_LOCATION_ROOM_COMPONENT)

    return hospital_models.Room.objects.get_or_create(id=room_id, ward=ward,
                                                      defaults={"name": room_id,
                                                                "date_of_activation": start_date,
                                                                "date_of_expiry": start_date + datetime.timedelta(
                                                                    weeks=1)})[0]


def get_or_create_bed(pv1_segment: hl7.Segment, room: hospital_models.Room,
                      start_date: datetime.datetime):
    bed_id = pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                       component_num=PATIENT_LOCATION_BED_COMPONENT)

    return hospital_models.Bed.objects.get_or_create(id=bed_id, room=room,
                                                     defaults={"name": bed_id,
                                                               "date_of_activation": start_date,
                                                               "date_of_expiry": start_date + datetime.timedelta(
                                                                   weeks=1)})[0]


def get_id_from_patient_location(pv1_segment: hl7.Segment, component_num: int):
    """Get the name from the given component and set to unique number, if it is empty."""

    name = pv1_segment.extract_field(field_num=PV1_PATIENT_LOCATION_FIELD,
                                     component_num=component_num)

    if name == "":
        name = str(uuid.uuid4()).replace("-", "")

    return name


def create_stay(pv1_segment: hl7.Segment, zbe_segment: hl7.Segment, visit: hospital_models.Visit,
                start_date: datetime.datetime):
    movement_id_string = zbe_segment.extract_field(field_num=ZBE_MOVEMENT_ID_FIELD)
    movement_id = int(movement_id_string)

    ward = get_or_create_ward(pv1_segment, start_date)
    room = get_or_create_room(pv1_segment, ward, start_date)
    bed = get_or_create_bed(pv1_segment, room, start_date)

    return hospital_models.Stay.objects.create(movement_id=movement_id, start_date=start_date, visit=visit,
                                               bed=bed, room=room, ward=ward)

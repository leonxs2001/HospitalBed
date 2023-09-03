import os
import shutil

import hl7
from django.test import TestCase
from django.utils import timezone

from dashboard.models import Stay
from dashboard.models.hospital_models import Bed, Visit, Room, Ward, Patient, Discharge
from dashboard.services import HL7MessageParser
from dashboard.services.hl7_services import AdmissionHL7Message, DischargeHL7Message, TransferHL7Message, \
    UpdateHL7Message, CancelTransferHL7Message, CancelDischargeHL7Message, CancelAdmissionHL7Message, HL7Message

directory_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_hl7_messages")
order_directory_path = os.path.join(directory_path, "test_order")


class TestAdmissionHL7Message(TestCase):
    """Unittest class for testing the AdmissionHl7Message class."""

    def test_parse_message(self):
        # test the parsing of an admission message without a given bed
        admission_without_bed_message = open(
            os.path.join(directory_path, "inpatient_admission_without_bed_message.hl7"), "r"
        ).read()
        admission_without_bed_message = admission_without_bed_message.replace("\n", "\r")
        admission_without_bed_message_instance = AdmissionHL7Message(hl7.parse(admission_without_bed_message))
        admission_without_bed_message_instance.parse_message()
        self.assertFalse(Stay.objects.filter(visit_id=5223045829).exists(),
                         msg="The admission message create a stay, although there is no given bed.")

        # test the parsing of an admission message with a given bed
        admission_message = open(os.path.join(directory_path, "inpatient_admission_message.hl7"), "r").read()
        admission_message = admission_message.replace("\n", "\r")
        admission_message_instance = AdmissionHL7Message(hl7.parse(admission_message))
        admission_message_instance.parse_message()
        self.assertTrue(Stay.objects.filter(visit_id=5223045829, end_date=None).exists(),
                        msg="The admission message does not create a stay.")


class TestTransferHL7Message(TestCase):
    """Unittest class for testing the TransferHl7Message class."""

    def test_parse_message(self):
        # test the parsing of a transfer message without a given bed
        transfer_without_bed_message = open(
            os.path.join(directory_path, "transfer_without_bed_message.hl7"), "r"
        ).read()
        transfer_without_bed_message = transfer_without_bed_message.replace("\n", "\r")
        transfer_without_bed_message_instance = TransferHL7Message(hl7.parse(transfer_without_bed_message))
        transfer_without_bed_message_instance.parse_message()
        self.assertFalse(Stay.objects.filter(visit_id=6223045829).exists(),
                         msg="The transfer message create a stay, although there is no given bed.")

        # test the parsing of a transfer message with a given bed
        transfer_message = open(
            os.path.join(directory_path, "transfer_message.hl7"), "r"
        ).read()
        transfer_message = transfer_message.replace("\n", "\r")
        transfer_message_instance = TransferHL7Message(hl7.parse(transfer_message))
        transfer_message_instance.parse_message()
        self.assertTrue(Stay.objects.filter(visit_id=6223045829, end_date=None).exists(),
                        msg="The transfer message does not create a stay.")

        transfer_message_instance.parse_message()
        self.assertTrue(Stay.objects.filter(visit_id=6223045829, end_date__isnull=False).exists(),
                        msg="The transfer message does not set the end_date for the last stay.")


class TestDischargeHL7Message(TestCase):
    """Unittest class for testing the DischargeHl7Message class."""

    def test_parse_message(self):
        # create the initial models for the test
        ward = Ward.objects.create(id="2", date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        room = Room.objects.create(id="2", ward=ward, date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        bed = Bed.objects.create(id="2", room=room, date_of_activation=timezone.now(), date_of_expiry=timezone.now())

        patient = Patient.objects.create(patient_id=2, sex=Patient.SexChoices.DIVERSE, date_of_birth=timezone.now())
        visit = Visit.objects.create(visit_id=7223045083, admission_date=timezone.now(), patient=patient)

        stay = Stay.objects.create(visit=visit, bed=bed, room=room, ward=ward, start_date=timezone.now(), movement_id=1)

        # test the parsing of a discharge message
        discharge_message = open(
            os.path.join(directory_path, "discharge_message.hl7"), "r"
        ).read()
        discharge_message = discharge_message.replace("\n", "\r")
        discharge_message_instance = DischargeHL7Message(hl7.parse(discharge_message))
        discharge_message_instance.parse_message()

        self.assertTrue(Visit.objects.filter(visit_id=visit.visit_id, discharge_date__isnull=False).exists(),
                        msg="The discharge message does not set the discharge_date for the visit.")

        self.assertTrue(Stay.objects.filter(visit=visit, movement_id=1, end_date__isnull=False).exists(),
                        msg="The discharge message does not set the end_date for the last stay.")

        self.assertTrue(Discharge.objects.filter(stay=stay, movement_id=1).exists(),
                        msg="The discharge message does not create a discharge for the stay with the movement_id.")


class TestUpdateHL7Message(TestCase):
    """Unittest class for testing the UpdateHl7Message class."""

    def test_parse_message(self):
        # create the initial patient for the test
        Patient.objects.create(patient_id=1441645, sex=Patient.SexChoices.FEMALE, date_of_birth=timezone.datetime.now())

        # test the parsing of an update message
        update_message = open(
            os.path.join(directory_path, "update_message.hl7"), "r"
        ).read()
        update_message = update_message.replace("\n", "\r")
        update_message_instance = UpdateHL7Message(hl7.parse(update_message))
        update_message_instance.parse_message()

        patient = Patient.objects.get(patient_id=1441645)
        self.assertEqual(patient.sex, Patient.SexChoices.MALE,
                         msg="The update message does not update the sex of a patient.")

        self.assertEqual(patient.date_of_birth, timezone.datetime(year=2000, month=1, day=1).date(),
                         msg="The update message does not update the date_of_birth of a patient.")


class TestCancelAdmissionHL7Message(TestCase):
    """Unittest class for testing the CancelAdmissionHl7Message class."""

    def test_parse_message(self):
        # create the initial models for the test
        ward = Ward.objects.create(id="3", date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        room = Room.objects.create(id="3", ward=ward, date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        bed = Bed.objects.create(id="3", room=room, date_of_activation=timezone.now(), date_of_expiry=timezone.now())

        patient = Patient.objects.create(patient_id=3, sex=Patient.SexChoices.DIVERSE, date_of_birth=timezone.now())
        visit = Visit.objects.create(visit_id=4223045827, admission_date=timezone.now(), patient=patient)

        stay = Stay.objects.create(visit=visit, bed=bed, room=room, ward=ward, start_date=timezone.now(), movement_id=1)

        # test the parsing of a cancel admission message
        cancel_admission_message = open(
            os.path.join(directory_path, "cancel_admission_message.hl7"), "r"
        ).read()
        cancel_admission_message = cancel_admission_message.replace("\n", "\r")
        cancel_admission_message_instance = CancelAdmissionHL7Message(hl7.parse(cancel_admission_message))
        cancel_admission_message_instance.parse_message()

        self.assertFalse(Stay.objects.filter(id=stay.id).exists(),
                         msg="The cancel admission message does not delete the stay from admission.")


class TestCancelTransferHL7Message(TestCase):
    """Unittest class for testing the CancelTransferHl7Message class."""

    def test_parse_message(self):
        # create the initial models for the test
        ward = Ward.objects.create(id="4", date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        room = Room.objects.create(id="4", ward=ward, date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        bed = Bed.objects.create(id="4", room=room, date_of_activation=timezone.now(), date_of_expiry=timezone.now())

        patient = Patient.objects.create(patient_id=4, sex=Patient.SexChoices.DIVERSE, date_of_birth=timezone.now())
        visit = Visit.objects.create(visit_id=8223023649, admission_date=timezone.now(), patient=patient)

        old_stay = Stay.objects.create(visit=visit, bed=bed, room=room, ward=ward, start_date=timezone.now(),
                                       movement_id=1, end_date=timezone.datetime.now())

        ward = Ward.objects.create(id="5", date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        room = Room.objects.create(id="5", ward=ward, date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        bed = Bed.objects.create(id="5", room=room, date_of_activation=timezone.now(), date_of_expiry=timezone.now())

        new_stay = Stay.objects.create(visit=visit, bed=bed, room=room, ward=ward, start_date=timezone.now(),
                                       movement_id=2)

        # test the parsing of a cancel transfer message
        cancel_transfer_message = open(
            os.path.join(directory_path, "cancel_transfer_message.hl7"), "r"
        ).read()
        cancel_transfer_message = cancel_transfer_message.replace("\n", "\r")
        cancel_transfer_message_instance = CancelTransferHL7Message(hl7.parse(cancel_transfer_message))
        cancel_transfer_message_instance.parse_message()

        self.assertTrue(Stay.objects.filter(id=old_stay.id, end_date=None).exists(),
                        msg="The cancel transfer message does not reset the end_date of the stay from before the transfer to None.")

        self.assertFalse(Stay.objects.filter(id=new_stay.id).exists(),
                         msg="The cancel transfer message does not delete the stay from the last transfer.")


class TestCancelDischargeHL7Message(TestCase):
    """Unittest class for testing the CancelDischargeHl7Message class."""

    def test_parse_message(self):
        # create the initial models for the test
        ward = Ward.objects.create(id="6", date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        room = Room.objects.create(id="6", ward=ward, date_of_activation=timezone.now(), date_of_expiry=timezone.now())
        bed = Bed.objects.create(id="6", room=room, date_of_activation=timezone.now(), date_of_expiry=timezone.now())

        patient = Patient.objects.create(patient_id=5, sex=Patient.SexChoices.DIVERSE, date_of_birth=timezone.now())
        visit = Visit.objects.create(visit_id=9223023649, admission_date=timezone.now(), discharge_date=timezone.now(),
                                     patient=patient)

        stay = Stay.objects.create(visit=visit, bed=bed, room=room, ward=ward, start_date=timezone.now(),
                                   movement_id=1, end_date=timezone.datetime.now())

        discharge = Discharge.objects.create(stay=stay, movement_id=2)

        # test the parsing of a cancel discharge message
        cancel_discharge_message = open(
            os.path.join(directory_path, "cancel_discharge_message.hl7"), "r"
        ).read()
        cancel_discharge_message = cancel_discharge_message.replace("\n", "\r")
        cancel_discharge_message_instance = CancelDischargeHL7Message(hl7.parse(cancel_discharge_message))
        cancel_discharge_message_instance.parse_message()

        self.assertFalse(Discharge.objects.filter(id=discharge.id).exists(),
                         msg="The cancel discharge message does not delete the discharge.")

        self.assertTrue(Stay.objects.filter(id=stay.id, end_date=None).exists(),
                        msg="The cancel discharge message does not reset the end_date of the stay from before the discharge to None.")

        self.assertTrue(Visit.objects.filter(visit_id=visit.visit_id, discharge_date=None).exists(),
                        msg="The cancel discharge message does not reset the discharge_date of the visit to None.")


class TestHL7MessageParser(TestCase):
    """Unittest class for testing the Hl7MessageParser class."""

    def test_create_hl7_message_from_string(self):
        """Tests the factory method create_hl7_message_from_string."""

        # test the right resulting instance from an inpatient admission message
        admission_message = open(os.path.join(directory_path, "inpatient_admission_message.hl7"), "r").read()
        admission_message = admission_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(admission_message),
                              AdmissionHL7Message, msg="ADT A01 message should return an AdmissionHl7Message.")

        # test the right resulting instance from a discharge message
        discharge_message = open(os.path.join(directory_path, "discharge_message.hl7"), "r").read()
        discharge_message = discharge_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(discharge_message),
                              DischargeHL7Message, msg="ADT A03 message should return a DischargeHl7Message.")

        # test the right resulting instance from a message for the change from in to outpatient
        in_to_out_patient_message = open(os.path.join(directory_path, "change_in_to_outpatient_message.hl7"),
                                         "r").read()
        in_to_out_patient_message = in_to_out_patient_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(in_to_out_patient_message),
                              DischargeHL7Message, msg="ADT A07 message should return a DischargeHl7Message.")

        # test the right resulting instance from a transfer message
        transfer_message = open(os.path.join(directory_path, "transfer_message.hl7"), "r").read()
        transfer_message = transfer_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(transfer_message),
                              TransferHL7Message, msg="ADT A02 message should return a TransferHl7Message.")

        # test the right resulting instance from an update message
        update_message = open(os.path.join(directory_path, "update_message.hl7"), "r").read()
        update_message = update_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(update_message),
                              UpdateHL7Message,
                              msg="ADT A08 message without an empty stay (end_date=None) should return a TransferHl7Message.")

        # test the right resulting instance from a cancel admission message
        cancel_admission_message = open(os.path.join(directory_path, "cancel_admission_message.hl7"), "r").read()
        cancel_admission_message = cancel_admission_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(cancel_admission_message),
                              CancelAdmissionHL7Message,
                              msg="ADT A11 message should return an CancelAdmissionHl7Message.")

        # test the right resulting instance from a cancel transfer message
        cancel_transfer_message = open(os.path.join(directory_path, "cancel_transfer_message.hl7"), "r").read()
        cancel_transfer_message = cancel_transfer_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(cancel_transfer_message),
                              CancelTransferHL7Message, msg="ADT A12 message should return a CancelTransferHl7Message.")

        # test the right resulting instance from a cancel discharge message
        cancel_discharge_message = open(os.path.join(directory_path, "cancel_discharge_message.hl7"), "r").read()
        cancel_discharge_message = cancel_discharge_message.replace("\n", "\r")
        self.assertIsInstance(HL7MessageParser._create_hl7_message_from_string(cancel_discharge_message),
                              CancelDischargeHL7Message,
                              msg="ADT A13 message should return a CancelDischargeHl7Message.")

        # test if messages without a usable message type or trigger event
        merge_message = open(os.path.join(directory_path, "merge_message.hl7"), "r").read()
        merge_message = merge_message.replace("\n", "\r")
        self.assertIsNone(HL7MessageParser._create_hl7_message_from_string(merge_message),
                          msg="ADT A40 message should not return a Hl7Message.")

        outpatient_admission_message = open(os.path.join(directory_path, "outpatient_admission_message.hl7"),
                                            "r").read()
        outpatient_admission_message = outpatient_admission_message.replace("\n", "\r")
        self.assertIsNone(HL7MessageParser._create_hl7_message_from_string(outpatient_admission_message),
                          msg="ADT A04 message should not return a Hl7Message.")

        out_to_inpatient_message = open(os.path.join(directory_path, "change_out_to_inpatient_message.hl7"), "r").read()
        out_to_inpatient_message = out_to_inpatient_message.replace("\n", "\r")
        self.assertIsNone(HL7MessageParser._create_hl7_message_from_string(out_to_inpatient_message),
                          msg="ADT A06 message should not return a Hl7Message.")

        no_adt_message = open(os.path.join(directory_path, "no_adt_message.hl7"), "r").read()
        no_adt_message = no_adt_message.replace("\n", "\r")
        self.assertIsNone(HL7MessageParser._create_hl7_message_from_string(no_adt_message),
                          msg="A message with a message type unequal to ADT should not return a Hl7Message.")

    def test_create_hl7_messages_from_file(self):
        """Tests the factory method create_hl7_messages_from_file."""

        # test the method with a file consisting of 2 messages
        # the returned list should have 2 Hl7Message elements
        hl7_messages = HL7MessageParser._create_hl7_messages_from_file(os.path.join(directory_path, "two_messages.hl7"))
        self.assertEqual(len(hl7_messages), 2,
                         msg="The method create_hl7_messages_from_file should return 2 Message " +
                             "if its given the two_messages.hl7 file.")

        self.assertIsInstance(hl7_messages[0], HL7Message,
                              msg="The returned list from the method create_hl7_messages_from_file " +
                                  "should only contain HL7Message-objects.")
        self.assertIsInstance(hl7_messages[1], HL7Message,
                              msg="The returned list from the method create_hl7_messages_from_file " +
                                  "should only contain HL7Message-objects.")

    def test_parse_hl7_messages_from_directory(self):
        """Tests the method parse_hl7_messages_from_directory."""

        # create a test directory and copy all important hl7 files in it
        new_directory = os.path.join(directory_path, "deletable_test_order")

        try:
            os.mkdir(new_directory)
        except FileExistsError:
            shutil.rmtree(new_directory)
            os.mkdir(new_directory)

        for filename in os.listdir(order_directory_path):
            if filename.endswith(".hl7"):
                source_path = os.path.join(order_directory_path, filename)
                destination_path = os.path.join(new_directory, filename)
                shutil.copy2(source_path, destination_path)

        # test the method with the created test directory
        # therefor test the right order of the parsing
        # and the deletion of all files in the end of the process
        HL7MessageParser.parse_hl7_messages_from_directory(new_directory)

        self.assertTrue(Discharge.objects.filter(stay__visit_id=4223045829).exists(),
                        msg="The messages are parsed in the wrong order.")

        self.assertEqual(len(os.listdir(new_directory)), 0,
                         msg="The method parse_hl7_message_from_directory should delete all hl7 messages at the end.")

        # delete the created test directory
        shutil.rmtree(new_directory)

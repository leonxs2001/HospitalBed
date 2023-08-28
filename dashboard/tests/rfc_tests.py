from django.test import TestCase
from django.utils import timezone

from dashboard.models import Ward, Room
from dashboard.models.hospital_models import Bed
from dashboard.services import RFCLocationParser


class TestRFCLocationParser(TestCase):
    def test_parse_wards(self):
        deletable_ward = Ward.objects.create(id="2", name="2",
                                             date_of_activation=timezone.datetime(year=2023, month=6, day=6),
                                             date_of_expiry=timezone.datetime(year=2050, month=6, day=6))

        ward_id = "1"
        ward_name = "Ward1"
        start_date_string = "20230606"
        end_date_string = "20500606"

        RFCLocationParser.parse_wards(
            [
                {"ORGID": ward_id,
                 "ORGNA": ward_name,
                 "BEGDT": start_date_string,
                 "ENDDT": end_date_string},
            ]
        )

        ward_exists = Ward.objects.filter(id=ward_id, name=ward_name,
                                          date_of_activation=timezone.datetime(year=2023, month=6, day=6),
                                          date_of_expiry=timezone.datetime(year=2050, month=6, day=6)).exists()
        self.assertTrue(ward_exists,
                        msg="The given ward is not created correctly.")

        self.assertFalse(Ward.objects.filter(id=deletable_ward.id).exists(),
                         "The not given ward in the list is not deleted.")

    def test_parse_rooms(self):
        ward = Ward.objects.create(id="A", name="Ward0", date_of_activation=timezone.datetime.now(),
                                   date_of_expiry=timezone.datetime.now())
        deletable_room = Room.objects.create(id="2", name="2", ward=ward,
                                             date_of_activation=timezone.datetime(year=2023, month=6, day=6),
                                             date_of_expiry=timezone.datetime(year=2050, month=6, day=6))
        room_id = "1"
        room_name = "Room1"

        start_date_string = "20230606"
        end_date_string = "20500606"

        RFCLocationParser.parse_rooms(
            [
                {"ZIMMERID": room_id,
                 "ZIMMERNAME": room_name,
                 "BEGDT": start_date_string,
                 "ENDDT": end_date_string,
                 "STATION": ward.id},
            ]
        )

        room_exists = Room.objects.filter(id=room_id, name=room_name, ward=ward,
                                          date_of_activation=timezone.datetime(year=2023, month=6, day=6),
                                          date_of_expiry=timezone.datetime(year=2050, month=6, day=6)).exists()
        self.assertTrue(room_exists,
                        msg="The given room is not created correctly.")

        self.assertFalse(Room.objects.filter(id=deletable_room.id).exists(),
                         "The not given room in the list is not deleted.")

    def test_parse_beds(self):
        ward = Ward.objects.create(id="A", name="Ward0", date_of_activation=timezone.datetime.now(),
                                   date_of_expiry=timezone.datetime.now())
        room = Room.objects.create(id="A", name="Room0", ward=ward,
                                   date_of_activation=timezone.datetime.now(),
                                   date_of_expiry=timezone.datetime.now())
        deletable_bed = Bed.objects.create(id="2", name="2", room=room,
                                           date_of_activation=timezone.datetime(year=2023, month=6, day=6),
                                           date_of_expiry=timezone.datetime(year=2050, month=6, day=6))
        bed_id = "1"
        bed_name = "Room1"

        start_date_string = "20230606"
        end_date_string = "20500606"

        RFCLocationParser.parse_beds(
            [
                {"BETTID": bed_id,
                 "BETTNAME": bed_name,
                 "BEGDT": start_date_string,
                 "ENDDT": end_date_string,
                 "ZIMMER": room.id},
            ]
        )

        bed_exists = Bed.objects.filter(id=bed_id, name=bed_name, room=room,
                                        date_of_activation=timezone.datetime(year=2023, month=6, day=6),
                                        date_of_expiry=timezone.datetime(year=2050, month=6, day=6)).exists()
        self.assertTrue(bed_exists,
                        msg="The given bed is not created correctly.")

        self.assertFalse(Bed.objects.filter(id=deletable_bed.id).exists(),
                         "The not given bed in the list is not deleted.")

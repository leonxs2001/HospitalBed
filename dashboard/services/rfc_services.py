import datetime

from django.utils import timezone
from pyrfc import Connection
from django.conf import settings
from django.db.utils import IntegrityError

from dashboard.models import Ward, Room
from dashboard.models.hospital_models import Bed

SAP_RFC_DATE_FORMAT = "%Y%m%d"


class RFCLocationParser:
    """A class for calling a sap system with rfc and parsing the results."""

    @classmethod
    def call_rfc_and_parse_result(cls):
        """Creates a connection to the sap system, calls the data with rfc and parses the returning locations."""
        time = timezone.now()

        conn = Connection(ashost=settings.ASHOST, sysnr=settings.SYSNR, client=settings.CLIENT, user=settings.USER,
                          passwd=settings.PASSWD)

        locations = conn.call('Z_RFC_READ_ORGIDS', I_EINRI="0001", I_DATE=time.strftime(SAP_RFC_DATE_FORMAT))

        cls.parse_wards(locations["ET_STATIONEN"])
        cls.parse_rooms(locations["ET_ZIMMER"])
        cls.parse_beds(locations["ET_BETTEN"])

    @classmethod
    def parse_wards(cls, ward_dicts):
        """Parses the wards in a given ward_dict, saves or updates them and deletes the not existing ones."""

        ward_ids = []

        # go through all wards and save or update them
        for ward_dict in ward_dicts:
            ward_id = ward_dict["ORGID"]

            ward_ids.append(ward_id)

            ward_name = ward_dict["ORGNA"]
            # set the ward_name to the ward_id if there is no given ward_name
            if not ward_name:
                ward_name = ward_id
            try:
                Ward.objects.update_or_create(
                    id=ward_id,
                    defaults={
                        "name": ward_name,
                        "date_of_activation": timezone.datetime.strptime(ward_dict["BEGDT"], SAP_RFC_DATE_FORMAT),
                        "date_of_expiry": timezone.datetime.strptime(ward_dict["ENDDT"], SAP_RFC_DATE_FORMAT)
                    })
            except IntegrityError:
                pass

        # delete all wards that are not contained in the given ward_dicts
        Ward.objects.exclude(id__in=ward_ids).delete()

    @classmethod
    def parse_rooms(cls, room_dicts):
        """Parses the rooms in a given room_dict, saves or updates them and deletes the not existing ones."""

        room_ids = []

        # go through all rooms and save or update them
        for room_dict in room_dicts:
            room_id = room_dict["ZIMMERID"]

            room_ids.append(room_id)

            room_name = room_dict["ZIMMERNAME"]
            # set the room_name to the room_id if there is no given room_name
            if not room_name:
                room_name = room_id
            try:
                Room.objects.update_or_create(
                    id=room_id,
                    defaults={
                        "name": room_name,
                        "ward_id": room_dict["STATION"],
                        "date_of_activation": timezone.datetime.strptime(room_dict["BEGDT"], SAP_RFC_DATE_FORMAT),
                        "date_of_expiry": timezone.datetime.strptime(room_dict["ENDDT"], SAP_RFC_DATE_FORMAT)
                    })
            except IntegrityError:
                pass

        # delete all rooms that are not contained in the given room_dicts
        Room.objects.exclude(id__in=room_ids).delete()

    @classmethod
    def parse_beds(cls, bed_dicts):
        """Parses the beds in a given bed_dict, saves or updates them and deletes the not existing ones."""

        bed_ids = []

        # go through all beds and save or update them
        for bed_dict in bed_dicts:
            bed_id = bed_dict["BETTID"]

            bed_ids.append(bed_id)

            bed_name = bed_dict["BETTNAME"]
            # set the bed_name to the bed_id if there is no given bed_name
            if not bed_name:
                bed_name = bed_id

            try:
                Bed.objects.update_or_create(
                    id=bed_id,
                    defaults={
                        "name": bed_name,
                        "room_id": bed_dict["ZIMMER"],
                        "date_of_activation": timezone.datetime.strptime(bed_dict["BEGDT"], SAP_RFC_DATE_FORMAT),
                        "date_of_expiry": timezone.datetime.strptime(bed_dict["ENDDT"], SAP_RFC_DATE_FORMAT)
                    })
            except IntegrityError:
                pass

        # delete all beds that are not contained in the given bed_dicts
        Bed.objects.exclude(id__in=bed_ids).delete()

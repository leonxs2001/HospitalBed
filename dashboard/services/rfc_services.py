import datetime

from django.utils import timezone
from pyrfc import Connection, ABAPApplicationError, ABAPRuntimeError, LogonError, CommunicationError
from django.conf import settings
from django.db.utils import IntegrityError

from dashboard.models import Ward, Room
from dashboard.models.hospital_models import Bed

SAP_RFC_DATE_FORMAT = "%Y%m%d"


class RFCLocationParser:
    @classmethod
    def call_rfc_and_parse_result(cls):
        time = timezone.now()
        conn = Connection(ashost=settings.ASHOST, sysnr=settings.SYSNR, client=settings.CLIENT, user=settings.USER,
                          passwd=settings.PASSWD)

        locations = conn.call('Z_RFC_READ_ORGIDS', I_EINRI="0001", I_DATE=time.strftime(SAP_RFC_DATE_FORMAT))
        cls.parse_wards(locations["ET_STATIONEN"])
        cls.parse_rooms(locations["ET_ZIMMER"])
        cls.parse_beds(locations["ET_BETTEN"])

    @classmethod
    def parse_wards(cls, ward_dicts):
        ward_ids = []

        for ward_dict in ward_dicts:
            ward_id = ward_dict["ORGID"]
            ward_ids.append(ward_id)

            ward_name = ward_dict["ORGNA"]
            if not ward_name:
                ward_name = ward_id

            Ward.objects.update_or_create(
                id=ward_id,
                defaults={
                    "name": ward_name,
                    "date_of_activation": timezone.datetime.strptime(ward_dict["BEGDT"], SAP_RFC_DATE_FORMAT),
                    "date_of_expiry": timezone.datetime.strptime(ward_dict["ENDDT"], SAP_RFC_DATE_FORMAT)
                })

        Ward.objects.exclude(id__in=ward_ids).delete()

    @classmethod
    def parse_rooms(cls, room_dicts):
        room_ids = []

        for room_dict in room_dicts:
            room_id = room_dict["ZIMMERID"]
            room_ids.append(room_id)
            room_name = room_dict["ZIMMERNAME"]
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
        Room.objects.exclude(id__in=room_ids).delete()

    @classmethod
    def parse_beds(cls, bed_dicts):
        bed_ids = []

        for bed_dict in bed_dicts:
            bed_id = bed_dict["BETTID"]
            bed_ids.append(bed_id)

            bed_name = bed_dict["BETTNAME"]
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

        Bed.objects.exclude(id__in=bed_ids).delete()

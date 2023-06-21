import datetime

from pyrfc import Connection, ABAPApplicationError, ABAPRuntimeError, LogonError, CommunicationError
from django.conf import settings

from dashboard.models.hospital_models import hospital_models

SAP_RFC_DATE_FORMAT = "%Y%m%d%H%M"
GERMAN_DATE_FORMAT = "%d.%m.%Y"


def call_sap_for_locations():
    time = datetime.datetime.now()
    conn = Connection(ashost=settings.ASHOST, sysnr=settings.SYSNR, client=settings.CLIENT, user=settings.USER,
                      passwd=settings.PASSWD)

    locations = conn.call('Z_RFC_READ_ORGIDS', I_EINRI="0001", I_DATE=time.strftime(SAP_RFC_DATE_FORMAT))

    parse_wards(locations["ET_STATIONEN"])
    parse_rooms(locations["ET_ZIMMER"])
    parse_beds(locations["ET_BETTEN"])


def parse_wards(ward_dicts):
    ward_ids = []

    for ward_dict in ward_dicts:
        ward_id = ward_dict["ORGID"]
        ward_ids.append(ward_id)
        hospital_models.Ward.objects.update_or_create(
            id=ward_id,
            defaults={
                "name": ward_dict["ORGNA"],  # TODO überprüfen
                "date_of_activation": datetime.datetime.strptime(ward_dict["BGDT"], GERMAN_DATE_FORMAT),
                "date_of_activation": datetime.datetime.strptime(ward_dict["ENDDT"], GERMAN_DATE_FORMAT)
            })

    hospital_models.Ward.objects.exclude(id__in=ward_ids).delete()


def parse_rooms(room_dicts):
    room_ids = []

    for room_dict in room_dicts:
        room_id = room_dict["ZIMMERID"]
        room_ids.append(room_id)
        hospital_models.Ward.objects.update_or_create(
            id=room_id,
            defaults={
                "name": room_dict["ZIMMERNAME"],
                "ward_id": room_dict["STATION"],
                "date_of_activation": datetime.datetime.strptime(room_dict["BGDT"], GERMAN_DATE_FORMAT),
                "date_of_activation": datetime.datetime.strptime(room_dict["ENDDT"], GERMAN_DATE_FORMAT)
            })

    hospital_models.Ward.objects.exclude(id__in=room_ids).delete()


def parse_beds(bed_dicts):
    bed_ids = []

    for bed_dict in bed_dicts:
        bed_id = bed_dict["BETTID"]
        bed_ids.append(bed_id)
        hospital_models.Ward.objects.update_or_create(
            id=bed_id,
            defaults={
                "name": bed_dict["BETTNAME"],
                "room_id": bed_dict["ZIMMER"],
                "date_of_activation": datetime.datetime.strptime(bed_dict["BGDT"], GERMAN_DATE_FORMAT),
                "date_of_activation": datetime.datetime.strptime(bed_dict["ENDDT"], GERMAN_DATE_FORMAT)
            })

    hospital_models.Ward.objects.exclude(id__in=bed_ids).delete()

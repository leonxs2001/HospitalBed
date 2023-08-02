import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from HospitalBed.settings import HL7_DIRECTORY
from dashboard.services import Hl7MessageParser, RFCLocationParser


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(Hl7MessageParser.parse_hl7_messages_from_directory, 'interval',
                      minutes=3, args=[HL7_DIRECTORY])
    scheduler.add_job(RFCLocationParser.call_rfc_and_parse_result, 'cron',
                      hour=0, minute=0)
    scheduler.start()
    atexit.register(scheduler.shutdown)

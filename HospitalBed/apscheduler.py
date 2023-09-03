import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from HospitalBed.settings import HL7_DIRECTORY
from dashboard.services import HL7MessageParser, RFCLocationParser


def start():
    """Starts the scheduled jobs for the application."""

    scheduler = BackgroundScheduler()

    scheduler.add_job(HL7MessageParser.parse_hl7_messages_from_directory, 'interval',
                      minutes=3, args=[HL7_DIRECTORY])
    scheduler.add_job(RFCLocationParser.call_rfc_and_parse_result, 'cron',
                      hour=0, minute=0)
    scheduler.start()

    # register a shutdown of the BackgroundScheduler in case of application shutdown
    atexit.register(scheduler.shutdown)

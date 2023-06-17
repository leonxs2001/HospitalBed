from pyrfc import Connection, ABAPApplicationError, ABAPRuntimeError, LogonError, CommunicationError
from configparser import ConfigParser
from pprint import PrettyPrinter

# host name of a specific SAP application server (ip oder domain name) -> sbb243.sbb.dom 10.243.7.243
ASHOST = 'sapxxxxx'
#  a self-contained commercial, organizational, and technical unit within an SAP System
# mandant --> 003
CLIENT = 'x00'
# a two-digit number between 00 to 99. SAP instances are numbered because system can contain more than once instance at a specific point of time.
#instanz nummber --> 00
SYSNR = '00'
USER = 'XXXXXXXX'
PASSWD = 'XXXXXXXX'
conn = Connection(ashost=ASHOST, sysnr=SYSNR, client=CLIENT, user=USER, passwd=PASSWD)

#Date format DD.MM.YYYY oder YYYYMMDD
try:
    result = None # Welcher datetyp? --> list

    # ET_STATION, ET_BETT, ET_FACHABTEILUNG, ET_ZIMMER
    conn.call('Z_RFC_READ_ORGIDS', I_EINRI="001", I_DATE="jetzigesDate",
              ET_FACHABTEILUNG=result, )

except CommunicationError:
    print("Could not connect to server.")
    raise
except LogonError:
    print("Could not log in. Wrong credentials?")
    raise
except (ABAPApplicationError, ABAPRuntimeError):
    print("An error occurred.")
    raise

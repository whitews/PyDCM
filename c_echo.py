import socket
import sys
import struct
from binascii import hexlify, unhexlify
from PDUItem import *
from PDU import *

### Implements DICOM A-ASSOCIATE-RQ and waits for response
### Not quite a complete C-ECHO yet.

USAGE = """
usage: c_echo.py host port peer_aet my_aet

Required arguments:
    host:     hostname of DICOM peer
    port:     tcp/ip port number of peer
    peer_aet: AE title of peer

Optional arguments:
    my_aet:   calling AE title (default: PyDCM-ECHO-SCU)
"""

if len(sys.argv) < 4:
    sys.exit(USAGE)

HOST       = sys.argv[1]
PORT       = int(sys.argv[2])
CALLED_AE  = sys.argv[3]
if len(sys.argv) == 5:
    CALLING_AE = sys.argv[4]
else:
    CALLING_AE = 'PyDCM-ECHO-SCU'

reserved   = unhexlify("00") # we'll use this a lot

###
### Method for processing response
###
def process_response(response):
    try:
        pdu_type   = hexlify(response[0])
        pdu_length = hexlify(response[2:6])
    except IndexError:
        sys.exit("Response from host was not a valid DICOM PDU.")
    
    #print hexlify(response)
    #print pdu_type
    
    if (int(pdu_length, 16) + 6) != len(response):
        sys.exit("A-ASSOCIATE response PDU length field not the length of PDU received.")
    
    if pdu_type == '02':
        return True
    
    return False

### Presentation Context Item:
###   Abstract Syntax: 1.2.840.10008.1.1 (Verification SOP Class UID)
###   Transfer Syntax: 1.2.840.10008.1.2 (Implicit VR Little Endian) 
presentation_context_items = []
presentation_context_items.append(PresentationContextItem(
        AbstractSyntaxItem('1.2.840.10008.1.1'), 
        TransferSyntaxItem('1.2.840.10008.1.2')))

associate_rq_pdu = AssociateRequestPDU(CALLED_AE, CALLING_AE, presentation_context_items)

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.send(associate_rq_pdu.render())
except:
    sys.exit("ERROR: Connection failed!!!")

# Now wait for a response, which can be either:
# - A-ASSOCIATE-AC (Accepted, PDU-type 02H)
# - A-ASSOCIATE-RJ (Rejected, PDU-type 03H)
#
# (3.8-2011, 7.1.2.1)
# We, the requestor, shall not issue any primitives except an A-ABORT 
# request primitive until we receive an A-ASSOCIATE confirmation primitive.
#
# The called AE shall accept or reject the association by sending an 
# A-ASSOCIATE response primitive with an appropriate Result parameter.

# Receive data from the server and shut down
response = sock.recv(1024)  

if process_response(response):
    print "Association request was accepted!"
else:
    print "Association request failed!"

sock.close()
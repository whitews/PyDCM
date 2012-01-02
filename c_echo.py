import socket
import sys
import struct
from binascii import hexlify, unhexlify

###
### Implements DICOM A-ASSOCIATE-RQ and waits for response
### Not quite a complete C-ECHO yet.
###
### Still need to finish parsing the response, and send an A-RELEASE request
###

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
    
    #print len(response)
    
    return False

### ASSOCIATE-RQ PDU fields:
### - PDU-type (1 byte)
### - Reserved (1 byte)
### - PDU-length (4 bytes)
### - Protocol-version (2 bytes)
### - Reserved (2 bytes)
### - Called-AE-title (16 bytes, w/leading or trailing spaces to fill)
### - Calling-AE-title (16 bytes, w/leading or trailing spaces to fill)
### - Reserved (32 bytes)
### - Variable items (variable length)
###
### Since the variable items have no specified length, we'll have to build them first
### then build the PDU
###
### Variable Items consist of the following:
### 1 Application Context Item
### 1 or more Presentation Context Item
### 1 User Information Item
###
### (see 2011 DICOM Standard, sections 7.1.1.2, 7.1.1.13, and 7.1.1.6)

### Application Context Item Fields (10H)
### DICOM Application Context Name is 1.2.840.10008.3.1.1.1 (3.7-2011, Annex A)
application_context_type = unhexlify('10')
application_context_name = "1.2.840.10008.3.1.1.1"

application_context_item  = application_context_type
application_context_item += reserved
application_context_item += unhexlify("%04x" % (len(application_context_name)))
application_context_item += application_context_name

### Presentation Context consists of 2 sub-items:
### - Abstract Syntax
### - Transfer Syntax
### We need to build these 2 sub-items first to calculate 
### the Presentation Context item length
###
### Also, we'll be sending only 1 presentation syntax for the 
### required transfer syntax Implicit VR Little Endian.

### Abstract Syntax Sub-Item Fields (30H)
abstract_syntax_type = unhexlify('30')
abstract_syntax_name = '1.2.840.10008.1.1' # Verification SOP Class UID

abstract_syntax_item  = abstract_syntax_type
abstract_syntax_item += reserved
abstract_syntax_item += unhexlify("%04x" % (len(abstract_syntax_name)))
abstract_syntax_item += abstract_syntax_name

### Transfer Syntax Sub-Item Fields (40H)
transfer_syntax_type = unhexlify('40')
transfer_syntax_name = '1.2.840.10008.1.2' # Implicit VR Little Endian Transfer Syntax

transfer_syntax_item  = transfer_syntax_type
transfer_syntax_item += reserved
transfer_syntax_item += unhexlify("%04x" % (len(transfer_syntax_name)))
transfer_syntax_item += transfer_syntax_name

### Presentation Context Item Fields (20H)
presentation_context_type = unhexlify('20')
presentation_context_id   = unhexlify('01')
presentation_context_item_length = len(
    presentation_context_id +
    (reserved * 3) +
    abstract_syntax_item +
    transfer_syntax_item)

presentation_context_item  = presentation_context_type
presentation_context_item += reserved
presentation_context_item += unhexlify("%04x" % (presentation_context_item_length))
presentation_context_item += presentation_context_id
presentation_context_item += reserved * 3
presentation_context_item += abstract_syntax_item
presentation_context_item += transfer_syntax_item

### User Information Sub-fields
### We need to build these before the User Information Item
### b/c we need to calculate the item length
###
### Maximum Length Sub-item Fields (51H)
### Max-length received allows association-requestor to restrict the max length
### of the variable field of the P-DATA-TF PDUs send by the acceptor on the
### association once established. Value is bytes encoded as an unsigned binary integer.
user_data_max_length_type = unhexlify("51")
user_data_max_length_recd = unhexlify("00004000") # set to 16,384 bytes

user_data_max_length_item  = user_data_max_length_type
user_data_max_length_item += reserved
user_data_max_length_item += unhexlify("%04x" % (len(user_data_max_length_recd)))
user_data_max_length_item += user_data_max_length_recd

### Implementation Class UID Sub-item Fields (52H)
implementation_class_uid_type = unhexlify("52")
implementation_class_uid = '2.25.155536688031' # '2.25.' plus some random gibberish

implementation_class_uid_item  = implementation_class_uid_type
implementation_class_uid_item += reserved
implementation_class_uid_item += unhexlify("%04x" % (len(implementation_class_uid)))
implementation_class_uid_item += implementation_class_uid

### Implementation Version Name Sub-item Fields (55H)
implementation_version_name_type = unhexlify("55")
implementation_version_name = 'PyDCM_0_0_1'

implementation_version_name_item  = implementation_version_name_type
implementation_version_name_item += reserved
implementation_version_name_item += unhexlify("%04x" % (len(implementation_version_name)))
implementation_version_name_item += implementation_version_name

### User Information Item Fields (50H)
### Now we can build the User Information Item from the sub-items
user_information_type = unhexlify('50')
user_information_item_length = len(
    user_data_max_length_item +
    implementation_class_uid_item +
    implementation_version_name_item)

user_information_item  = user_information_type
user_information_item += reserved
user_information_item += unhexlify("%04x" % (user_information_item_length))
user_information_item += user_data_max_length_item
user_information_item += implementation_class_uid_item
user_information_item += implementation_version_name_item

###
### Finally, we can build the whole PDU!!!
###
PDU_type         = unhexlify("01") # ASSOCIATE-RP
protocol_version = unhexlify("0001") # version 1

# Remember, the AE title fields must be 16 bytes, padding with spaces if necessary
if len(CALLED_AE) != 16:
    for i in range(16 - len(CALLED_AE)):
        CALLED_AE += unhexlify('20')
if len(CALLING_AE) != 16:
    for i in range(16 - len(CALLING_AE)):
        CALLING_AE += unhexlify('20')

PDU_length = len(
    protocol_version +
    (reserved * 2) +
    CALLED_AE +
    CALLING_AE +
    (reserved *32) +
    application_context_item +
    presentation_context_item +
    user_information_item)

PDU  = PDU_type
PDU += reserved
PDU += unhexlify("%08x" % (PDU_length))
PDU += protocol_version
PDU += reserved * 2
PDU += CALLED_AE
PDU += CALLING_AE
PDU += reserved * 32
PDU += application_context_item
PDU += presentation_context_item # should be a list, since there can be more than 1
PDU += user_information_item

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.send(PDU)
except:
    sys.exit("ERROR: Connection failed!!!")

# Now sit back, put our feet up, and wait for a response which can be either:
# - A-ASSOCIATE-AC (Accepted, PDU-type 02H)
# - A-ASSOCIATE-RJ (Rejected, PDU-type 03H)
#
# (3.8-2011, 7.1.2.1)
# We, the requestor, shall not issue any primitives except an A-ABORT request 
# primitive until we receive an A-ASSOCIATE confirmation primitive.
#
# The called AE shall accept or reject the association by sending an A-ASSOCIATE 
# response primitive with an appropriate Result parameter.

# Receive data from the server and shut down
received = sock.recv(1024)  
sock.close()

if process_response(received):
    print "Association request was accepted!"
else:
    print "Association request failed!"

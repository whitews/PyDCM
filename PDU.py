from PDUItem import *
from binascii import hexlify, unhexlify

# Defines classes for the 7 DICOM PDUs
#
# The DICOM Standard Part 3.8-2011, Section 9.3.1
#
# The Protocol Data Units (PDUs) are the message formats exchanged between peer 
# entities within a layer. A PDU shall consist of protocol control information 
# and user data. PDUs are constructed by mandatory fixed fields followed by 
# optional variable fields which contain one or more items and/or sub-items.
#
# Items of unrecognized types shall be ignored and skipped. Items shall appear 
# in an increasing order of their item types. Several instances of the same 
# item shall be acceptable or shall not as specified by each item.
#
# The DICOM UL protocol consists of seven Protocol Data Units:
# a)	A-ASSOCIATE-RQ
# b)	A-ASSOCIATE-AC
# c)	A-ASSOCIATE-RJ
# d)	P-DATA-TF
# e)	A-RELEASE-RQ
# f)	A-RELEASE-RP
# g)	A-ABORT



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
### Variable Items consist of the following:
### - 1 Application Context Item (10H)
### - 1 or more Presentation Context Items (20H) [Contains Sub-Items]
###     - Abstract Syntax Sub-Item (30H)
###     - Transfer Syntax Sub-Item (40H)
### - 1 User Information Item (50H) [Contains Sub-Items]
###     - Maximum Length (51H)
###     - Implementation Class UID (52H)
###     - Implementation Version Name (55H)
### (see 2011 DICOM Standard, sections 7.1.1.2, 7.1.1.13, and 7.1.1.6)
# A-ASSOCIATE-RQ PDU (01H) - Part 3.8-2011, Table 9-11
class AssociateRequestPDU:
    def __init__(self, called_ae, calling_ae, presentation_context_items):
        self.PDU_type                   = unhexlify("01") # ASSOCIATE-RQ
        self.protocol_version           = unhexlify("0001") # version 1
        
        # Need to pad AETs with spaces to 16 bytes
        if len(called_ae) != 16:
            for i in range(16 - len(called_ae)):
                called_ae += unhexlify('20')
        if len(calling_ae) != 16:
            for i in range(16 - len(calling_ae)):
                calling_ae += unhexlify('20')
        self.called_ae                  = called_ae
        self.calling_ae                 = calling_ae
        
        self.application_context_item   = ApplicationContextItem()
        
        self.presentation_context_items = []
        for item in presentation_context_items:
            self.presentation_context_items.append(item)
        
        self.user_information_item      = UserInformationItem(
                                            MaximumLengthItem(),
                                            ImplementationClassUIDItem(),
                                            ImplementationVersionNameItem())
    
    def getLength(self):
        presentation_context_items_length = 0
        for item in self.presentation_context_items:
            presentation_context_items_length += len(item.render())
        
        PDU_length = len(
            self.protocol_version +
            (reserved * 2) +
            self.called_ae +
            self.calling_ae +
            (reserved *32) +
            self.application_context_item.render() +
            self.user_information_item.render())
            
        PDU_length += presentation_context_items_length
        
        return PDU_length
    
    def render(self):
        PDU  = self.PDU_type
        PDU += reserved
        PDU += unhexlify("%08x" % (self.getLength()))
        PDU += self.protocol_version
        PDU += reserved * 2
        PDU += self.called_ae
        PDU += self.calling_ae
        PDU += reserved * 32
        PDU += self.application_context_item.render()
        for item in self.presentation_context_items:
            PDU += item.render()
        PDU += self.user_information_item.render()
        
        return PDU
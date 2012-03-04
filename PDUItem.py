from binascii import hexlify, unhexlify

reserved   = unhexlify("00") # we'll use this a lot

### Application Context Item (10H)
### DICOM Application Context Name is 1.2.840.10008.3.1.1.1 (3.7-2011, Annex A)
class ApplicationContextItem:
    def __init__(self):
        self.item_type = unhexlify('10')
        self.item_name = "1.2.840.10008.3.1.1.1"
        self.item_desc = "ApplicationContextItem"
    
    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (len(self.item_name)))
        item += self.item_name
        
        return item
    
    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H): ' + self.item_name

### Presentation Context Item (20H)
### Consists of 2 sub-items:
### - Abstract Syntax
### - Transfer Syntax
class PresentationContextItem:
    def __init__(self, abstract_syntax_item, transfer_syntax_item):
        self.item_type            = unhexlify('20')
        self.item_context_id      = unhexlify('01')
        self.item_desc            = "PresentationContextItem"
        self.abstract_syntax_item = abstract_syntax_item
        self.transfer_syntax_item = transfer_syntax_item

    def getLength(self):
        item_length = len(
            self.item_context_id +
            (reserved * 3) +
            self.abstract_syntax_item.render() +
            self.transfer_syntax_item.render())
        
        return item_length

    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (self.getLength()))
        item += self.item_context_id
        item += reserved * 3
        item += self.abstract_syntax_item.render()
        item += self.transfer_syntax_item.render()
        
        return item

    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H)'

### Abstract Syntax Sub-Item (30H)
class AbstractSyntaxItem:
    def __init__(self, abstract_syntax_uid):
        self.item_type = unhexlify('30')
        self.item_name = abstract_syntax_uid # should check for valid UIDs
        self.item_desc = "AbstractSyntaxItem"

    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (len(self.item_name)))
        item += self.item_name
        
        return item

    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H): ' + self.item_name

### Transfer Syntax Sub-Item (40H)
class TransferSyntaxItem:
    def __init__(self, transfer_syntax_uid):
        self.item_type = unhexlify('40')
        self.item_name = transfer_syntax_uid # should check for valid UIDs
        self.item_desc = "TransferSyntaxItem"

    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (len(self.item_name)))
        item += self.item_name
        
        return item

    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H): ' + self.item_name

### User Information Item Fields (50H)
class UserInformationItem:
    def __init__(self, max_length_item, implementation_class_uid_item,  implementation_version_name_item):
        self.item_type                        = unhexlify('50')
        self.item_desc                        = "UserInformationItem"
        self.max_length_item                  = max_length_item
        self.implementation_class_uid_item    = implementation_class_uid_item
        self.implementation_version_name_item = implementation_version_name_item

    def getLength(self):
        item_length = len(
            self.max_length_item.render() +
            self.implementation_class_uid_item.render() +
            self.implementation_version_name_item.render())
        
        return item_length

    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (self.getLength()))
        item += self.max_length_item.render()
        item += self.implementation_class_uid_item.render()
        item += self.implementation_version_name_item.render()
        
        return item

    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H)'

### Maximum Length Sub-item (51H)
### Max-length received allows association-requestor to restrict the max length
### of the variable field of the P-DATA-TF PDUs send by the acceptor on the
### association once established. Value is bytes encoded as an unsigned binary integer.
class MaximumLengthItem:
    def __init__(self):
        self.item_type  = unhexlify('51')
        self.max_length = unhexlify("00004000") # set to 16,384 bytes
        self.item_desc  = "MaximumLengthItem"

    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (len(self.max_length)))
        item += self.max_length
        
        return item

    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H): ' + self.max_length

### Implementation Class UID Sub-item (52H)
class ImplementationClassUIDItem:
    def __init__(self):
        self.item_type = unhexlify('52')
        self.item_name = '2.25.155536688031' # '2.25.' plus some random gibberish
        self.item_desc = "ImplementationClassUIDItem"

    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (len(self.item_name)))
        item += self.item_name
        
        return item

    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H): ' + self.item_name

### Implementation Version Name Sub-item (55H)
class ImplementationVersionNameItem:
    def __init__(self):
        self.item_type = unhexlify('55')
        self.item_name = 'PyDCM_0_0_1' # Identify our implementation
        self.item_desc = "ImplementationVersionNameItem"

    def render(self):
        item  = self.item_type
        item += reserved
        item += unhexlify("%04x" % (len(self.item_name)))
        item += self.item_name
        
        return item

    def __str__(self):
        return self.item_desc + ' (' + hexlify(self.item_type) + 'H): ' + self.item_name

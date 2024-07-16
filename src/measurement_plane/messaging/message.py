from measurement_plane.messaging.message_format import MessageFields
from datetime import datetime

class Message:
    def __init__(self) -> None:
        self.message = {}
        self.construct_base()
    
    def construct_base(self):
        self.message = {
            MessageFields.LABEL: None,
            MessageFields.ENDPOINT: None,
            MessageFields.CAPABILITY_NAME: None,
            MessageFields.PARAMETERS_SCHEMA: None,
            MessageFields.RESULT_SCHEMA: None,
            MessageFields.TIMESTAMP: None,
            MessageFields.NONCE: None,
            MessageFields.METADATA: None
        }
        

class CapabilityMessage(Message):
    def __init__(self) -> None:
        super().__init__()
    
    def construct(self, label=None, endpoint = None, capability_name = None ,parameters_schema=None, result_schema=None, nonce = None, metadata = None, type = None):
        self.message[MessageFields.LABEL] = label
        self.message[MessageFields.ENDPOINT] = endpoint
        self.message[MessageFields.CAPABILITY_NAME] = capability_name
        self.message[MessageFields.PARAMETERS_SCHEMA] = parameters_schema
        self.message[MessageFields.RESULT_SCHEMA] = result_schema
        self.message[MessageFields.TIMESTAMP] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        self.message[MessageFields.NONCE] = nonce
        self.message[MessageFields.METADATA] = metadata
        self.message[MessageFields.CAPABILITY] = type


from measurement_plane.messaging.message import CapabilityMessage
from measurement_plane.messaging.message_format import MessageFields

class BaseCapability:
    """
    Capability Base Class
    """

    def __init__(self, name:str):
        self.name = name
        self.agent = None
        self.endpoint = None
        self.label = None
        self.parameters_schema = None
        self.result_schema = None
        self.nonce = None
        self.metadata = None
        self.type = None

    def set_agent(self, agent):
        self.agent = agent
        self.endpoint = agent.endpoint

    def construct_capability(self):
        capability = CapabilityMessage()
        capability.construct(
            label=self.label,
            endpoint=self.endpoint,
            capability_name=self.name,
            parameters_schema=self.parameters_schema,
            result_schema=self.result_schema,
            nonce=self.nonce,
            metadata=None,
            type=self.type
        )
        self.message = capability.message
        return capability.message  # construct capability message
    
    def send_result(self, operation_id, result_values):
        raise NotImplementedError("This method should be overridden by subclasses")
    
    def execute_task(self, parameters):
        raise NotImplementedError("This method should be overridden by subclasses")

    
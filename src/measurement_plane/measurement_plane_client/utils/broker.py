import time
import threading
import json
from measurement_plane.messaging.message import Message
import logging
from measurement_plane.protocols.amqp.receive import ReceiverThread
from measurement_plane.protocols.amqp.send import Sender
from measurement_plane.messaging.message_format import Topics

CAPABILITY_TIMEOUT = 60
CLEANUP_INTERVAL = 10

# Configure logging
#logging.basicConfig(level=logging.INFO)  # Set the desired logging level

class CapabilitiesManager:
    def __init__(self, timeout, cleanup_interval):
        self.capabilities = {}
        self.last_update = {}
        self.timeout = timeout
        self.cleanup_interval = cleanup_interval
        self.lock = threading.Lock()
        
        # Start the thread to periodically remove stale capabilities
        self.cleanup_thread = threading.Thread(target=self._run_cleanup, daemon=True)
        self.cleanup_thread.start()

    def add_capability(self, capability_id, capability_msg):        
        with self.lock:
            if capability_id not in self.capabilities:
                self.capabilities[capability_id] = {}

            # Add the capability to the dictionary using its ID
            self.capabilities[capability_id] = capability_msg
            
            # Update the last update time
            self.last_update[capability_id] = time.time()

    def remove_stale_capabilities(self):
        current_time = time.time()
        ids_to_remove = []
        
        with self.lock:
            for endpoint, last_time in self.last_update.items():
                if current_time - last_time > self.timeout:
                    ids_to_remove.append(endpoint)
            
            for endpoint in ids_to_remove:
                del self.capabilities[endpoint]
                del self.last_update[endpoint]

    def _run_cleanup(self):
        while True:
            self.remove_stale_capabilities()
            time.sleep(self.cleanup_interval)


    def get_capability(self, capability_id):
        return self.capabilities.get(capability_id)



class Broker():
    def __init__(self, broker_url):
        self.broker_url = broker_url
        self.capability_manager = CapabilitiesManager(CAPABILITY_TIMEOUT, CLEANUP_INTERVAL)
        self.sender = Sender()
    def start(self):
        self.receiver_capabilities = ReceiverThread(broker_url=self.broker_url, topic=Topics.CAPABILITIES_TOPIC, on_message_callback=self.receiver_capabilities_on_message_callback)
        self.receiver_capabilities.start()

    def receiver_capabilities_on_message_callback(self, event):
        try:
            message =json.loads(event.message.body)
            capability_id = Message.calculate_capability_id(message=message)
            capability = message
            logging.info(f"recived capability: {capability}")
            self.capability_manager.add_capability(capability_id, capability)
        except Exception as e:
            logging.error(f"Error processing message: {e}")
    



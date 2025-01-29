import random
import string
import json, pickle
import logging
from datetime import datetime
from threading import Thread, Event
from jsonschema import validate, exceptions as jsonschema_exceptions
from measurement_plane.protocols.amqp.receive import ReceiverThread
from measurement_plane.protocols.amqp.send import Sender
from measurement_plane.messaging.message import Message
from measurement_plane.measurement_plane_client.utils.broker import Broker
import time
from measurement_plane.messaging.message_format import MessageFields
class MeasurementPlaneClient:
    def __init__(self, broker_url) -> None:
        self.broker_url = broker_url
        self.sender = Sender()
        self.broker = Broker(self.broker_url)
        self.broker.start()


    def get_capabilities(self, capability_types: list = None) -> dict:
        capabilities = self.broker.capability_manager.capabilities
        if capability_types:
            keys_to_delete = [cp_id for cp_id in capabilities if capabilities[cp_id][MessageFields.CAPABILITY] not in capability_types]
            for cp_id in keys_to_delete:
                del capabilities[cp_id]
        return capabilities

    def combine_to_string(self, attributes: list) -> str:
        return ''.join(str(att).replace(" ", "").replace("\n", "") for att in attributes)
    
    def calculate_capability_id(self, message):
        return Message.calculate_capability_id(message=message)

    def create_measurement(self, capability: dict) -> 'Measurement':
        return Measurement(capability, self)

    def send_measurement(self, measurement: 'Measurement'):
        if measurement.valid:
            spec_endpoint = measurement.specification_message["endpoint"]
            specification_topic = f'topic://{spec_endpoint}/specifications'
            reply_to_topic = 'topic://' + ''.join(random.choices(string.ascii_letters + string.digits, k=10))

            measurement.receipt_receiver = ReceiverThread(broker_url=self.broker_url, topic = reply_to_topic, on_message_callback=measurement.receipt_receiver_on_message_callback)
            measurement.receipt_receiver.start()

            self.sender.send(self.broker_url, specification_topic, measurement.specification_message, reply_to_topic)

            measurement.receipt_receiver.thread.join(timeout=5)
            measurement.receipt_receiver.stop()
            logging.info("Measurement sent")
        else:
            logging.error("Measurement not valid for sending")
            pass

    def interrupt_measurement(self, measurement: 'Measurement'):
        measurement.interrupt()

class Measurement:
    def __init__(self, capability: dict, measurement_plane_client: MeasurementPlaneClient):
        self.measurement_plane_client = measurement_plane_client
        self.broker_url = self.measurement_plane_client.broker_url
        self.capability = capability
        self.results_receiver = None
        self.receipt_receiver = None
        self.results = []
        self.config = {}
        self.specification_message = capability.copy()
        self.specification_message[MessageFields.SPECIFICATION] = self.specification_message.pop(MessageFields.CAPABILITY)
        self.valid = False

    def configure(self, schedule: dict, parameters: dict, result_callback, stream_results: bool = False, redirect_to_storage: bool = False, completion_callback = None) -> bool:
        if self.validate_parameters(parameters):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
            self.specification_message.update({
                MessageFields.PARAMETERS: parameters,
                MessageFields.SCHEDULE: schedule,
                MessageFields.TIMESTAMP: timestamp
            })
            self.config = {
                "stream_results": stream_results,
                "redirect_to_storage": redirect_to_storage,
                "result_callback": result_callback,
                "completion_callback": completion_callback
            }
            self.valid = True
        else:
            self.valid= False

    def receipt_receiver_on_message_callback(self, event):
        receipt_msg = json.loads(event.message.body)
        if MessageFields.RECEIPT in receipt_msg:
            event.container.stop()
            if  MessageFields.INTERRUPT in receipt_msg:
                logging.info("Measurement interrupted.")
            else:
                if receipt_msg[MessageFields.RECEIPT] == 'store':
                    pass
                elif self.results_receiver is None:
                    if self.config['redirect_to_storage']:
                        store_capabilities = self.measurement_plane_client.get_capabilities(["store"])
                        store_capability = None
                        for sc in store_capabilities:
                            store_capability = store_capabilities[sc]
                        if store_capability:
                            storage_measurement = self.measurement_plane_client.create_measurement(store_capability)
                            label = self.specification_message[MessageFields.ENDPOINT]
                            measurement_id = Message.calculate_measurement_id(message = receipt_msg)
                            topic = f'topic://{measurement_id}/results'
                            command = "start"
                            parameters = {
                                "label": label,
                                "topic": topic,
                                "command": command
                            }
                            schedule =self.specification_message[MessageFields.SCHEDULE]
                            if "|stream" in schedule:
                                schedule = schedule.replace("|stream", "")
                            storage_measurement.configure(
                                schedule=schedule,
                                parameters=parameters,
                                result_callback=None,  # Callback function for new results
                            )
                            self.measurement_plane_client.send_measurement(storage_measurement)                    
                    measurement_id = Message.calculate_measurement_id(message = receipt_msg)
                    topic = f'topic://{measurement_id}/results'
                    #topic = f'topic:///test/results'
                    self.results_receiver = ReceiverThread(broker_url=self.broker_url, topic = topic, on_message_callback=self.result_receiver_on_message_callback)
                    self.results_receiver.start()

    def result_receiver_on_message_callback(self, event):
        message_body = event.message.body

        # Convert memoryview to bytes if necessary
        if isinstance(message_body, memoryview):
            message_body = message_body.tobytes()

        # Try to decode as JSON or fall back to pickle
        result_msg = None
        if isinstance(message_body, bytes):
            # If it's bytes, assume it's pickled binary data
            try:
                result_msg = pickle.loads(message_body)
                logging.info("Successfully received and deserialized the message using pickle.")
            except pickle.UnpicklingError as e:
                logging.error(f"Failed to deserialize message with pickle: {e}")
                result_msg = None
        else:
            try:
                result_msg = json.loads(message_body)
                logging.info("Successfully received and decoded the message using JSON.")
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as e:
                logging.error(f"Failed to decode message as JSON: {e}")
                result_msg = None

        # Proceed if decoding was successful
        if result_msg and 'result' in result_msg:
            results = result_msg['resultValues']
            if 'EOF_results' in results:
                print("EOF received will stop")
                self.stop()
                return
            self.config['result_callback'](results)
            
    def interrupt(self):
        interrupt_msg = self.specification_message
        interrupt_msg[MessageFields.CAPABILITY] = interrupt_msg[MessageFields.SPECIFICATION]
        interruption = Measurement(interrupt_msg, self.measurement_plane_client)
        interruption.valid = True
        interrupt_msg = interruption.specification_message
        interrupt_msg[MessageFields.INTERRUPT] = interrupt_msg[MessageFields.SPECIFICATION]
        del interrupt_msg[MessageFields.SPECIFICATION]
        interruption.message = interrupt_msg
        self.measurement_plane_client.send_measurement(interruption)
        self.stop()
        
    def stop(self):
        print("will close the receiver")
        self.results_receiver.stop()
            

    def validate_parameters(self, parameters: dict) -> bool:
        try:
            validate(instance=parameters, schema=self.capability[MessageFields.PARAMETERS_SCHEMA])
            return True
        except jsonschema_exceptions.ValidationError as err:
            logging.error(f"Validation error: {err.message}")
            return False

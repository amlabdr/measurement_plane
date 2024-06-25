import logging, json
from protocols.amqp.receive import Receiver
from protocols.amqp.send import Sender
from datetime import datetime
from threading import Thread, Event
from ..utils.message import Message

class MeasurementAgent:
    def __init__(self, config):
        self.config = config
        self.sender = Sender()
        self.running_measurements = {}

    def send_receipt(self, event):
        receipt_msg=json.loads(event.message.body)
        if "specification" in receipt_msg:
            receipt_msg['receipt'] = receipt_msg['specification']
            del receipt_msg['specification']
        elif "interrupt" in receipt_msg:
            receipt_msg['receipt'] = receipt_msg['interrupt']
        else:
            logging.warning("Recipt not supported for msg: {}".format(receipt_msg))
        receipt_msg["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        topic_reply_to =  event.message.reply_to
        url = self.config.amqp_broker
        self.sender.send(url, topic = topic_reply_to, messages= receipt_msg)

    def subscribe_to_telemetry_service(self):
        endpoint = self.config.capability["endpoint"]
        topic='topic://'+endpoint+'/specifications'
        url = self.config.amqp_broker
        logging.info("Agent will start lesstning for events from the telemetry service")
        receiver = Receiver(on_message_callback=self.telemetry_service_on_message_callback)
        receiver.receive_event(url,topic)

    def process_specification(self, specification_msg, interrupt_event):
        logging.info("Processing of specification starts: {}")
        while not interrupt_event.is_set():
            data = ""
            self.send_result(specification_msg, data)
            
    def send_result(self, specification_msg, results):
        result_msg = specification_msg.copy()
        measurement_id = Message.calculate_measurement_id(result_msg)
        result_msg['result'] = result_msg['specification']
        result_msg["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        del result_msg['specification']
        resultValues= []
        resultValues.append(results)
        result_msg['resultValues'] = resultValues
        result_topic = 'topic://'+str(measurement_id)+'/results'
        url = self.config.amqp_broker
        self.sender.send(url, topic = result_topic, messages= result_msg)
        print("Result {} sent to {}".format(resultValues, result_topic))

    def telemetry_service_on_message_callback(self, event):
        specification_msg =json.loads(event.message.body)     
        logging.info("Recived msg: {}".format(specification_msg))
        if "specification" in specification_msg:
            self.send_receipt(event)
            spec_name = specification_msg['specification']
            measurement_id = Message.calculate_measurement_id(specification_msg)
            operation_id = Message.calculate_operation_id(specification_msg)
            if measurement_id not in self.running_measurements:
                self.running_measurements[measurement_id] = {
                        'operation_ids': [],
                        'measurement_process': (None, None)
                    }
                self.running_measurements[measurement_id]['operation_ids'].append(operation_id)
                interrupt_event = Event()
                thread = Thread(target=self.process_specification, args=(specification_msg, interrupt_event))
                self.running_measurements[measurement_id]['measurement_process'] = (thread, interrupt_event)
                thread.start()

            if operation_id not in self.running_measurements[measurement_id]['operation_ids']:
                self.running_measurements[measurement_id]['operation_ids'].append(operation_id)

        elif 'interrupt' in specification_msg:
            self.send_receipt(event)
            spec_name = specification_msg['interrupt']
            measurement_id = specification_msg.calculate_measurement_id()
            operation_id = specification_msg.calculate_operation_id()
            if measurement_id in self.running_measurements:
                if operation_id in self.running_measurements[measurement_id]['operation_ids']:
                    self.running_measurements[measurement_id]['operation_ids'].remove(operation_id)
                else:
                    logging.warning(f"Specification {spec_name} not found.")
                if len(self.running_measurements[measurement_id]['operation_ids']) == 0:
                    thread, interrupt_event = self.running_measurements[measurement_id]['measurement_process']
                    interrupt_event.set()
                    thread.join()
                    del self.running_measurements[measurement_id]
                    logging.info(f"Interrupt signal sent for specification {spec_name}")
                    
            else:
                logging.warning(f"Specification {spec_name} not found.")
            
        else:
            logging.warning("Unknown message type.")



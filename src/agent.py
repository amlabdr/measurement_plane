import logging
import json
import time
import threading
from datetime import datetime
from threading import Thread, Event
from src.utils.decorators import registered_capabilities
from src.base_capability import BaseCapability
from src.protocols.amqp.receive import Receiver
from src.protocols.amqp.send import Sender
from src.messaging.message_format import Topics, MessageFields, Ids, TaskSchedule
class Agent:
    def __init__(self, broker : str, endpoint : str):
        self.broker = broker
        self.endpoint = endpoint
        self.capabilities = []
        self.running = False
        self.sender = Sender()
        self.running_measurements = {}

    def load_capabilities(self):
        """
        Load and register all capabilities that have been decorated.
        """
        for capability_cls in registered_capabilities:
            capability_instance = capability_cls()
            self.register_capability(capability_instance)
    
    def register_capability(self, capability:BaseCapability):
        self.capabilities.append(capability)
        capability.set_agent(self)  # Provide capability a reference to the agent

    def advertise_capabilities(self):
        topic = Topics.CAPABILITIES_TOPIC
        while self.running:
            for capability in self.capabilities:
                message = capability.construct_capability()
                self.sender.send(self.broker, topic, message)
                #logging.info(f"agent sent capability :{message}")
            time.sleep(10)  # Advertise every 10 seconds

    def start(self):
        self.load_capabilities()
        if self.capabilities:
            self.running = True
            advertise_thread = threading.Thread(target=self.advertise_capabilities)
            advertise_thread.start()

            topic = Topics.get_specifications_topic(self.endpoint)
            logging.info("Agent will start lesstning for events")
            receiver = Receiver(on_message_callback=self.handle_messages)
            receiver.receive_event(self.broker, topic)
            self.running = False
            return self.running
        else:
            self.running = False
            return self.running
        
    def stop(self):
        self.running = False
        
    def handle_messages(self, event):
        specification_msg =json.loads(event.message.body)
        capability_id = Ids.calculate_capability_id(specification_msg)
        capability = None
        for cap in self.capabilities:
            if capability_id == Ids.calculate_capability_id(cap.construct_capability()):
                capability = cap
                break

        if capability:
            logging.info("Recived msg: {}".format(specification_msg))
            if MessageFields.SPECIFICATION in specification_msg:
                self.send_receipt(event)
                measurement_id = Ids.calculate_measurement_id(specification_msg)
                operation_id = Ids.calculate_operation_id(specification_msg)
                if measurement_id not in self.running_measurements:
                    self.running_measurements[measurement_id] = {
                            'operation_ids': [],
                            'measurement_process': (None, None)
                        }
                    self.running_measurements[measurement_id]['operation_ids'].append(operation_id)
                    interrupt_event = Event()
                    thread = Thread(target=self.process_specification, args=(specification_msg, interrupt_event, capability))
                    self.running_measurements[measurement_id]['measurement_process'] = (thread, interrupt_event)
                    thread.start()

                if operation_id not in self.running_measurements[measurement_id]['operation_ids']:
                    self.running_measurements[measurement_id]['operation_ids'].append(operation_id)

            elif MessageFields.INTERRUPT in specification_msg:
                self.send_receipt(event)
                measurement_id = Ids.calculate_measurement_id(specification_msg)
                operation_id = Ids.calculate_operation_id(specification_msg)
                if measurement_id in self.running_measurements:
                    if operation_id in self.running_measurements[measurement_id]['operation_ids']:
                        self.running_measurements[measurement_id]['operation_ids'].remove(operation_id)
                    else:
                        logging.warning(f"Specification not found.")
                    if len(self.running_measurements[measurement_id]['operation_ids']) == 0:
                        thread, interrupt_event = self.running_measurements[measurement_id]['measurement_process']
                        interrupt_event.set()
                        thread.join()
                        logging.info(f"Interrupt signal sent for specification")
                        
                else:
                    logging.warning(f"Specification not found.")
                
            else:
                logging.warning("Unknown message type.")
        else:
            logging.info("received unknown capability")
        

    def send_receipt(self, event):
        receipt_msg=json.loads(event.message.body)
        if MessageFields.SPECIFICATION in receipt_msg:
            receipt_msg[MessageFields.RECEIPT] = receipt_msg[MessageFields.SPECIFICATION]
            del receipt_msg[MessageFields.SPECIFICATION]
        elif MessageFields.INTERRUPT in receipt_msg:
            receipt_msg[MessageFields.RECEIPT] = receipt_msg[MessageFields.INTERRUPT]
        else:
            logging.warning("Recipt not supported for msg: {}".format(receipt_msg))
        receipt_msg[MessageFields.TIMESTAMP] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        topic_reply_to =  event.message.reply_to
        self.broker
        self.sender.send(self.broker, topic = topic_reply_to, messages= receipt_msg)

    def process_specification(self, specification_msg : dict, interrupt_event : Event, capability : BaseCapability):
        schedule = specification_msg[MessageFields.SCHEDULE]
        task_schedule = TaskSchedule(schedule)
        parameters = specification_msg[MessageFields.PARAMETERS]
        # Wait until the start time, or until interrupted or stopped
        while datetime.now() < task_schedule.start:
            if interrupt_event.is_set():
                logging.info("Interrupt event set before start time, stopping process.")
                return
            if not self.running:
                logging.info("self.running is False before start time, stopping process.")
                return
            # Sleep for a short duration to avoid busy-waiting
            time.sleep(0.1)
        #SCHEDULE RUNNING TIME CRON
        # Execute the task and check stop conditions
        while self.running:
            if interrupt_event.is_set():
                logging.info("Interrupt event set, stopping process.")
                break
            if task_schedule.stop:
                if datetime.now() > task_schedule.stop:
                    logging.info("Current time is past stop time, stopping process.")
                    break

            results = capability.execute_task(parameters=parameters)
            if results:
                self.send_result(specification_msg, results)

            if not task_schedule.periodicity:
                break
            else:
                time.sleep(task_schedule.periodicity.total_seconds())
        
        measurement_id = Ids.calculate_measurement_id(specification_msg)
        del self.running_measurements[measurement_id]
        self.send_result(specification_msg, MessageFields.EOF_RESULTS)
            
    def send_result(self, specification_msg, results):
        result_msg = specification_msg.copy()
        measurement_id = Ids.calculate_measurement_id(result_msg)
        result_msg[MessageFields.RESULT] = result_msg[MessageFields.SPECIFICATION]
        result_msg[MessageFields.TIMESTAMP] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        del result_msg[MessageFields.SPECIFICATION]
        resultValues= []
        resultValues.append(results)
        result_msg[MessageFields.RESULT_VALUES] = resultValues
        result_topic = Topics.get_results_topic(str(measurement_id))
        self.sender.send(self.broker, topic = result_topic, messages= result_msg)
        logging.info("Result {} sent to {}".format(resultValues, result_topic))


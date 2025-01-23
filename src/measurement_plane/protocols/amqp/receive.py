#standards imports
import traceback, logging, threading

#imports to use AMQP 1.0 communication protocol
from proton.handlers import MessagingHandler
from proton.reactor import Container

"""class Receiver():
    def __init__(self, on_message_callback=None):
        self.on_message_callback = on_message_callback
        self.handler = None
        self.container = None

    def receive_event(self, server, topic):
        self.handler = self.event_Receiver_handller(server, topic, self.on_message_callback)
        self.container = Container(self.handler)
        self.container.run()
    
    def stop(self):
        if self.handler:
            self.handler.stop()
        if self.container:
            self.container.stop()
        print("stoped normally the handler and container")

    class event_Receiver_handller(MessagingHandler):
        def __init__(self, server, topic, on_message_callback=None):
            super(Receiver.event_Receiver_handller, self).__init__()
            self.server = server
            self.topic = topic
            self.on_message_callback = on_message_callback
            self.connection = None
            #logging.info("Agent will start listening for events in the topic: {}".format(self.topic))

        def on_start(self, event):
            self.connection = event.container.connect(self.server)
            event.container.create_receiver(self.connection, self.topic)

        def on_message(self, event):
            try:
                # Acknowledge the message
                event.delivery.update(event.delivery.ACCEPTED)
                event.delivery.settle()
                # Call the custom on_message callback if provided
                if self.on_message_callback:
                    self.on_message_callback(event)

            except Exception:
                traceback.print_exc()
        
        def on_disconnected(self, event):
            logging.warning("Disconnected from server: {}".format(self.server))
        
        def stop(self):
            self.connection.close()
"""

class ReceiverThread:
    def __init__(self, broker_url, topic, on_message_callback=None):
        self.receiver = PersistentReceiver(broker_url, topic, on_message_callback)
        self.container = Container(self.receiver)
        self.thread = threading.Thread(target=self.container.run)
        self.thread.daemon = True  # Ensure thread doesn't prevent program exit

    def start(self):
        self.thread.start()

    def stop(self):
        self.receiver.stop()
        
class PersistentReceiver(MessagingHandler):
    def __init__(self, broker_url, topic, on_message_callback=None):
        super().__init__()
        self.broker_url = broker_url
        self.topic = topic
        self.on_message_callback = on_message_callback
        self.connection = None

    def on_start(self, event):
        self.connection = event.container.connect(self.broker_url)
        event.container.create_receiver(self.connection, self.topic)

    def on_message(self, event):
        try:
            # Acknowledge the message
            event.delivery.update(event.delivery.ACCEPTED)
            event.delivery.settle()
            # Call the custom on_message callback if provided
            if self.on_message_callback:
                self.on_message_callback(event)

        except Exception:
            traceback.print_exc()
    
    def on_disconnected(self, event):
        logging.warning("Disconnected from server: {}".format(self.broker_url))

    def stop(self):
        self.connection.close()


from measurement_agent.measurement_agent import MeasurementAgent
import logging
import time

class CustomMeasurementAgent(MeasurementAgent):
    def __init__(self, config):
        super().__init__(config)
        # Custom init

    def process_specification(self, specification_msg, interrupt_event):
        logging.info(f"Processing of specification starts: {specification_msg}")
        while not interrupt_event.is_set():
            # Custom processing logic
            #do some measurement or some operation
            data = "processed data"
            self.send_result(specification_msg, data)
            time.sleep(1)  # Simulate processing delay

    # You can customize/add any function to the MeasurementAgent Here

from utils.config import Config

if __name__ == "__main__":
    # Define the configuration
    amqp_broker = "your_amqp_broker_url"
    capability = {
        "endpoint": "your_endpoint"
    }
    config = Config(amqp_broker, capability)

    # Initialize and start the measurement agent
    agent = CustomMeasurementAgent(config)
    agent.subscribe_to_telemetry_service()

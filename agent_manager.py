import logging
import time
import argparse
import os
from src.agent import Agent
from capabilities import *

logging.basicConfig(level=logging.INFO)

"""
Agent Lifecycle Management
"""
def start_agent():
    parser = argparse.ArgumentParser(description="Start the agent with custom capabilities.")
    parser.add_argument("--broker", type=str, default=os.getenv("BROKER_URL", "http://129.6.254.164:5672/"),
                        help="Broker URL for the agent")
    parser.add_argument("--endpoint", type=str, default=os.getenv("ENDPOINT", "/multiverse/qnet/coincidences"),
                        help="Endpoint for the agent")
    args = parser.parse_args()

    agent = Agent(broker=args.broker, endpoint=args.endpoint)
    
    try:
        agent.start()
        logging.info("Agent started successfully. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping agent...")
        agent.stop()
        logging.info("Agent stopped successfully.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        agent.stop()

if __name__ == "__main__":
    start_agent()

# Measurement Plane

**Measurement Plane** is a Python library for creating customizable measurement agents with standardized capabilities. This system is primarily designed for scientists who need a scalable, structured way to configure, run, and monitor scientific measurements via capabilities that advertise, receive tasks, and return measurement data.

## Table of Contents
1. [Features](#features)
2. [Getting Started](#getting-started)
3. [Installation](#installation)
4. [Usage](#usage)
   - [Defining Custom Capabilities](#defining-custom-capabilities)
   - [Starting the Agent](#starting-the-agent)
5. [Configuration](#configuration)
6. [Project Structure](#project-structure)
7. [Examples](#examples)
8. [Contributing](#contributing)

---

## Features

- **Customizable Measurement Capabilities**: Easily define custom measurement capabilities.
- **Agent Lifecycle Management**: Manages agents through a lifecycle, from startup to data processing.
- **Messaging and Task Execution**: Handles messaging seamlessly and allows easy integration of task execution.
- **Scalable Architecture**: Supports multiple capabilities and allows streaming or single measurements, depending on the task needs.

## Getting Started

### Prerequisites

- Python 3.6 or higher.
- Libraries listed in `requirements.txt` (detailed in the installation section).

## Installation

Clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd measurement_plane
pip install -r requirements.txt
python setup.py install
```

## Usage

### Defining Custom Capabilities

Capabilities are specialized measurement modules. To define a capability, create a class that inherits from `BaseCapability` and implements specific measurement logic. Each capability requires:

- **Name**: A unique identifier for the capability.
- **Parameters Schema**: Defines the expected parameters for the measurement, such as channels or measurement duration.
- **Result Schema**: Describes the expected output format of the measurement results.

Here’s a generic example of how to structure a capability:

```python
from measurement_plane.base_capability import BaseCapability
from measurement_plane.utils.decorators import capability

@capability
class CustomMeasurementCapability(BaseCapability):
    def __init__(self):
        super().__init__(name="custom_measurement_capability")
        self.label = "Custom Measurement Capability"
        # Define the schema for input parameters
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "example_param": {
                    "type": "string",
                    "description": "Description of the parameter"
                }
            }
        }
        # Define the schema for output results
        self.result_schema = {...}

    def stream(self, parameters):
        # Implement measurement logic here
        ...
    
    def execute_task(self, parameters):
        # Implement task execution logic here
        ...
```

This class defines a new capability with customized input and output schemas. You can add any measurement logic within the measure or execute_task methods.

### Starting the Agent

To run the agent with customizable broker and endpoint settings, use the following code in your main script:

```python
import time
import argparse
import os
from measurement_plane.agent import Agent
from capabilities import *

"""
Agent Lifecycle Management
"""
def start_agent():
    # Define command-line arguments for broker and endpoint
    parser = argparse.ArgumentParser(description="Start the agent with custom capabilities.")
    parser.add_argument(
        "--broker", 
        type=str, 
        default=os.getenv("BROKER_URL", "http://localhost:5672/"), 
        help="Broker URL for the agent (default: http://localhost:5672/)"
    )
    parser.add_argument(
        "--endpoint", 
        type=str, 
        default=os.getenv("ENDPOINT", "/default/endpoint"), 
        help="Endpoint for the agent (default: /default/endpoint)"
    )
    args = parser.parse_args()

    # Initialize the agent with specified broker and endpoint
    agent = Agent(broker=args.broker, endpoint=args.endpoint)

    try:
        agent.start()
        logging.info("Agent started successfully. Press Ctrl+C to stop.")
        # Keep the agent running
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
```
This setup will start the agent, which advertises its capabilities, listens on the broker endpoint, and waits for incoming tasks.

#### Customizing Broker and Endpoint

- **Broker URL**: The broker URL can be specified through an environment variable `BROKER_URL` or using the `--broker` argument when running the script. The default value is `"http://localhost:5672/"`.
- **Endpoint**: The endpoint for the agent can be set with the `ENDPOINT` environment variable or via the `--endpoint` argument. It defaults to `"/default/endpoint"`.

This flexible configuration allows you to easily deploy the agent across different environments and setups.

## Configuration

The agent can be configured to connect to different broker URLs and endpoints. These configurations can be set using environment variables or command-line arguments.

- **Broker URL**: Specifies the URL of the message broker that the agent connects to for communication. By default, it is set to `"http://localhost:5672/"`. You can override this by:
  - Setting the `BROKER_URL` environment variable, or
  - Using the `--broker` argument when starting the agent script.

- **Endpoint**: Defines the specific endpoint path for the agent within the broker. This is set to `"/default/endpoint"` by default. You can change it by:
  - Setting the `ENDPOINT` environment variable, or
  - Using the `--endpoint` argument in the agent’s start command.

### Example Usage

To start the agent with a custom broker and endpoint, you can use:

```bash
python your_script.py --broker "http://your-broker-url:port/" --endpoint "/your/endpoint/path"
```
Or, you can set environment variables before running the script:
```bash
export BROKER_URL="http://your-broker-url:port/"
export ENDPOINT="/your/endpoint/path"
python your_script.py
```
This configuration setup allows you to adapt the agent for various deployment environments and requirements.

## Project Structure

The project is organized as follows:

```plaintext
measurement_plane/
├── src/                          # Source code directory
│   ├── measurement_plane/         # Main package for measurement_plane
│   │   ├── agent.py               # Core agent logic
│   │   ├── base_capability.py     # Base class for defining capabilities
│   │   ├── utils/                 # Utility functions and helper modules
│   │   └── ...                    # Other modules and components
├── requirements.txt               # Dependency file for required Python packages
├── setup.py                       # Installation script for packaging and distributing the library
├── README.md                      # Project documentation (this file)
└── examples/                      # Example scripts demonstrating usage of capabilities and agent setup
```

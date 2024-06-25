import hashlib

class Message:
    @staticmethod
    def calculate_capability_id(message):
        try:
            endpoint = message["endpoint"]
            capability_name = message["capabilityName"]
            combined_string = Message.combine_to_string([endpoint, capability_name])
            capability_id = hashlib.sha256(combined_string.encode()).hexdigest()
            return capability_id
        except KeyError as e:
            raise KeyError(f"Missing required field: {e}")
        except Exception as e:
            raise Exception(f"An error occurred while calculating capability ID: {e}")

    @staticmethod
    def calculate_measurement_id(message):
        try:
            capability_id = Message.calculate_capability_id(message)
            parameters = message["parameters"]
            schedule = message["schedule"]
            combined_string = Message.combine_to_string([capability_id, parameters, schedule])
            measurement_id = hashlib.sha256(combined_string.encode()).hexdigest()
            return measurement_id
        except KeyError as e:
            raise KeyError(f"Missing required field: {e}")
        except Exception as e:
            raise Exception(f"An error occurred while calculating measurement ID: {e}")

    @staticmethod
    def calculate_operation_id(message):
        try:
            measurement_id = Message.calculate_measurement_id(message)
            nonce = message["nonce"]
            timestamp = message["timestamp"]
            combined_string = Message.combine_to_string([measurement_id, nonce, timestamp])
            operation_id = hashlib.sha256(combined_string.encode()).hexdigest()
            return operation_id
        except KeyError as e:
            raise KeyError(f"Missing required field: {e}")
        except Exception as e:
            raise Exception(f"An error occurred while calculating operation ID: {e}")

    @staticmethod
    def combine_to_string(attributes: list) -> str:
        combined_string = ""
        for att in attributes:
            # Convert dictionary to string, remove spaces and newlines
            att_str = str(att).replace(" ", "").replace("\n", "")
            combined_string += att_str
        return combined_string

# Test the Message class
def test_message_class():
    message = {
        "endpoint": {"url": "http://example.com/api", "method": "POST"},
        "capabilityName": {"name":     "sendData"
                           , "version": "1.0"},
        "parameters": {"param1": "value1", "param2": "value2"},
        "schedule": {"interval": "5m"},
        "timestamp": "2024-06-1312:34:56Z",
        "nonce": "1234567890abcdef"
    }

    capability_id = Message.calculate_capability_id(message)
    measurement_id = Message.calculate_measurement_id(message)
    operation_id = Message.calculate_operation_id(message)

    print(f"Capability ID: {capability_id}")
    print(f"Measurement ID: {measurement_id}")
    print(f"Operation ID: {operation_id}")

#test_message_class()

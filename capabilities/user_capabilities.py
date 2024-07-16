import logging
from src.base_capability import BaseCapability
from src.utils.decorators import capability

import pytz
from datetime import datetime

logging.basicConfig(level=logging.INFO)

@capability
class regionTimeCapability(BaseCapability):
    def __init__(self):
        super().__init__(name="region_time_capability")
        self.label = "region time Capability"
        self.parameters_schema = {
                                    "type": "object",
                                    "properties": {
                                        "region": {
                                            "type": "string",
                                            "description": "The region of requested time"
                                        }
                                    }
                                }

        self.result_schema = {
                                "type": "object",
                                "properties": {
                                    "region": {
                                        "type": "string",
                                        "description": "The region of requested time"
                                    },
                                    "local time": {
                                        "type": "string",
                                        "description": "The local time"
                                    }
                                }
                            }
        self.nonce = '12345'
        self.type = 'measure'

    def execute_task(self, parameters):
        region = parameters.get("region")
        if region:
            try:
                # Get the current time in UTC
                utc_time = datetime.now(pytz.utc)
                
                # Convert the time to the specified region's local time
                local_time = utc_time.astimezone(pytz.timezone(region))
                
                # Format the time as a string
                local_time_str = local_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
                
                return {"region":region, "local time": local_time_str}
            except pytz.UnknownTimeZoneError:
                return {"region":f"Unknown region {region}", "local time": ""}
        else:
            return {"region":"Region not specified", "local time": ""}

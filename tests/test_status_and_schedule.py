import asyncio
import json
import unittest

from measurement_plane.agent import Agent
from measurement_plane.measurement_plane_client.mp_client import Measurement
from measurement_plane.messaging.message_format import (
    ExecutionModes,
    LifecycleStates,
    MessageFields,
    MessageTypes,
    TaskSchedule,
)


class DummyClient:
    broker_url = "nats://example.invalid:4222"

    def __init__(self):
        self.broker_client = self
        self.unsubscribed = []

    async def unsubscribe(self, key):
        self.unsubscribed.append(key)


class RecordingBroker:
    def __init__(self):
        self.messages = []

    async def publish(self, subject, message):
        self.messages.append((subject, json.loads(message)))


class StatusAndScheduleTests(unittest.TestCase):
    def test_stream_execution_mode_does_not_corrupt_schedule(self):
        capability = {
            MessageFields.CAPABILITY: "measure-count-rate",
            MessageFields.ENDPOINT: "/timetagger/alice",
            MessageFields.CAPABILITY_NAME: "count_rate_measurement",
            MessageFields.PARAMETERS_SCHEMA: {"type": "object"},
            MessageFields.METADATA: {},
        }
        measurement = Measurement(capability, DummyClient())

        measurement.configure("now", {}, lambda _: None, stream_results=True)

        self.assertEqual(measurement.specification_message[MessageFields.SCHEDULE], "now")
        self.assertEqual(
            measurement.specification_message[MessageFields.EXECUTION_MODE],
            ExecutionModes.INFINITE_STREAM,
        )

    def test_legacy_and_canonical_stream_schedules_are_parsed(self):
        self.assertEqual(TaskSchedule("now| stream").stream, "active")
        self.assertEqual(TaskSchedule("now||stream").stream, "active")

    def test_status_message_includes_reason_and_source(self):
        agent = Agent("nats://example.invalid:4222", "/timetagger/alice")
        broker = RecordingBroker()
        agent.broker_client = broker
        specification = {
            MessageFields.ENDPOINT: "/timetagger/alice",
            MessageFields.CAPABILITY_NAME: "count_rate_measurement",
            MessageFields.EXECUTION_MODE: ExecutionModes.INFINITE_STREAM,
        }

        asyncio.run(agent.send_lifecycle_event(
            specification,
            "measurement-1",
            "measurement_failed",
            LifecycleStates.FAILED,
            {
                MessageFields.ERROR: "device disconnected",
                MessageFields.ERROR_TYPE: "RuntimeError",
            },
        ))

        _, message = broker.messages[0]
        self.assertEqual(message[MessageFields.MESSAGE_TYPE], MessageTypes.MEASUREMENT_STATUS)
        self.assertEqual(message[MessageFields.STATUS], LifecycleStates.FAILED)
        self.assertEqual(message[MessageFields.ERROR], "device disconnected")
        self.assertEqual(message[MessageFields.ERROR_TYPE], "RuntimeError")
        self.assertEqual(message[MessageFields.SOURCE][MessageFields.ENDPOINT], "/timetagger/alice")

    def test_eof_waits_for_terminal_lifecycle_status(self):
        async def scenario():
            client = DummyClient()
            capability = {
                MessageFields.CAPABILITY: "test",
                MessageFields.ENDPOINT: "/test",
                MessageFields.CAPABILITY_NAME: "test",
                MessageFields.PARAMETERS_SCHEMA: {"type": "object"},
            }
            events = []
            measurement = Measurement(capability, client)
            measurement.configure("now", {}, lambda _: None, completion_callback=lambda: None, lifecycle_callback=events.append)
            measurement.result_subscription = "results"
            measurement.event_subscription = "events"

            async def delayed_failure():
                await asyncio.sleep(0.01)
                await measurement._event_handler("status", None, json.dumps({
                    MessageFields.LIFECYCLE_EVENT: "measurement_failed",
                    MessageFields.LIFECYCLE_STATE: LifecycleStates.FAILED,
                    MessageFields.ERROR: "downstream unavailable",
                }))

            task = asyncio.create_task(delayed_failure())
            await measurement._result_handler("results", None, json.dumps({
                MessageFields.RESULT: "test",
                MessageFields.RESULT_VALUES: [MessageFields.EOF_RESULTS],
            }))
            await task
            self.assertEqual(measurement.state, LifecycleStates.FAILED)
            self.assertEqual(events[0][MessageFields.ERROR], "downstream unavailable")
            self.assertEqual(client.unsubscribed, ["results", "events"])

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()

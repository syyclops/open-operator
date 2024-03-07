from openoperator.infrastructure import MQTTClient, Timescale
from openoperator.domain.model import PointReading
import re
import json
from datetime import datetime, timezone

class MQTTService:
  def __init__(self, mqtt_client: MQTTClient, ts: Timescale):
    self.mqtt_client = mqtt_client
    self.ts = ts
    self.mqtt_client.client.on_message = self.on_mqtt_message

  def start(self):
    self.mqtt_client.start()

  def on_mqtt_message(self, client, userdata, message):
    topic = message.topic
    print(f"Received message on topic {topic}")
    print(f"Message payload: {message.payload}")
    # shelly iot plug pattern
    shelly_plug_pattern = r"shellyplugus.*events/rpc"
    shelly_status_switch_pattern = r"shellyplugus.*status/switch:0"

    if re.match(shelly_plug_pattern, topic):
      # Ensure safe decoding of the message payload from bytes to str, then load as JSON
      try:
        data = json.loads(message.payload.decode())
        ts = datetime.fromtimestamp(data["params"]["ts"] , tz=timezone.utc).isoformat() # Extract the timestamp
        
        # Dynamically handle extraction of other parameters if needed
        # Iterate through each key in "params" to find "switch:X" objects
        for key, value in data["params"].items():
          if key.startswith("switch"):
            # Extract the "id" and iterate over each measurement key within the switch object
            switch_id = value["id"]
            for measurement_key in value:
              if measurement_key in ["current", "voltage"]:
                # Construct the timeseries ID
                timeseriesId = f"{data['src']}-switch-{switch_id}-{measurement_key}"
                measurement_value = value[measurement_key]
                point_reading = PointReading(ts=ts, value=measurement_value, timeseriesid=timeseriesId)
                print(f"Inserting timeseries: {point_reading}")
                self.ts.insert_timeseries([point_reading])
      except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
      except KeyError as e:
        print(f"Missing expected key in data: {e}")
    elif re.match(shelly_status_switch_pattern, topic):
      print("Shelly switch status message received")
      try:
        data = json.loads(message.payload.decode())
        # Extracting 'minute_ts' from 'aenergy' as timestamp
        ts = data["aenergy"]["minute_ts"]
        ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        output = data["output"]
        
        # Construct the timeseries ID
        timeseriesId = topic
        point_reading = PointReading(ts=ts, value=output, timeseriesid=timeseriesId)
        print(f"Inserting timeseries: {point_reading}")
        self.ts.insert_timeseries([point_reading])
      except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
      except KeyError as e:
        print(f"Missing expected key in data: {e}")
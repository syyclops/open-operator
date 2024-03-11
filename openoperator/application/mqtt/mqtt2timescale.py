from openoperator.infrastructure import MQTTClient, Timescale, Postgres
from openoperator.domain.model import PointReading
from threading import Lock, Timer
from typing import List
import atexit
import re
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

class MQTT2Timescale:
  """
  This is a application that listens to messages from the broker and stores them in the database.
  - message processing
  - batch processing
  - flushing the batch to the database
  """
  def __init__(self, mqtt_client: MQTTClient, ts: Timescale, batch_size=100, flush_interval=30):
    self.mqtt_client = mqtt_client
    self.ts = ts
    self.mqtt_client.client.on_message = self.on_mqtt_message
    self.batch_size = batch_size
    self.flush_interval = flush_interval
    self.batch: List[PointReading] = []
    self.batch_lock = Lock()
    self.flush_timer = None
    self.reset_flush_timer()

  def start_message_listener(self, topic: str):
    """
    Used to start listening to messages then store them in the database.
    """
    self.mqtt_client.connect()
    self.mqtt_client.subscribe(topic)
    self.mqtt_client.loop_forever()

  def stop(self):
    """
    Used to stop the message listener and flush the batch to the database.
    """
    if self.flush_timer:
      self.flush_timer.cancel()
    self.flush_batch()
    self.mqtt_client.stop()

  def reset_flush_timer(self):
    """
    Used to reset the flush timer.
    """
    if self.flush_timer:
      self.flush_timer.cancel()
    self.flush_timer = Timer(self.flush_interval, self.flush_batch)
    self.flush_timer.start()

  def flush_batch(self):
    with self.batch_lock:
      if self.batch:
        # Insert the batch into the database
        self.ts.insert_timeseries(self.batch)
        print(f"Flushed {len(self.batch)} messages to the database.")
        self.batch.clear()
      self.reset_flush_timer()

  def on_mqtt_message(self, client, userdata, message):
    """
    Process the message and store it in the batch.
    """
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
        ts = datetime.fromtimestamp(data["params"]["ts"]).isoformat() # Extract the timestamp
        
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
                with self.batch_lock:
                  self.batch.append(point_reading)
                  if len(self.batch) >= self.batch_size:
                    self.flush_batch()
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
        ts = datetime.fromtimestamp(ts).isoformat()
        output = data["output"]
        
        # Construct the timeseries ID
        timeseriesId = topic
        point_reading = PointReading(ts=ts, value=output, timeseriesid=timeseriesId)
        with self.batch_lock:
          self.batch.append(point_reading)
          if len(self.batch) >= self.batch_size:
            self.flush_batch()
      except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
      except KeyError as e:
        print(f"Missing expected key in data: {e}")

mqtt_client = MQTTClient()
postgres = Postgres()
timescale = Timescale(postgres=postgres)

app = MQTT2Timescale(mqtt_client=mqtt_client, ts=timescale)

app.start_message_listener(topic="#")

def on_exit():
  app.stop()
  mqtt_client.disconnect()

atexit.register(on_exit)
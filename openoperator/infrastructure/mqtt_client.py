import paho.mqtt.client as paho
from paho import mqtt
import os

class MQTTClient:
  """
  This mqtt client is responsible for:
  - connection management to the broker
  - authentication
  - subscribing to topics
  - publishing messages
  - error handling and logging TODO
  """
  def __init__(self, host: str | None = None, username: str | None = None, password: str | None = None, port=8883):
    self.host = host if host is not None else os.getenv('MQTT_BROKER_ADDRESS')
    self.port = port
    self.username = username if username is not None else os.getenv('MQTT_USERNAME')
    self.password = password if password is not None else os.getenv('MQTT_PASSWORD')
    self.client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id="", userdata=None, protocol=paho.MQTTv5)
    self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    self.client.username_pw_set(username=self.username, password=self.password)
    self.client.on_connect = self.on_connect

  def connect(self):
    self.client.connect(self.host, self.port, 60)

  def on_connect(self, client, userdata, flags, rc, properties=None):
    print("Connected to MQTT broker with result code "+str(rc))

  def publish(self, topic: str, payload: str):
    try:
      self.client.publish(topic, payload)
    except Exception as e:
      raise e

  def subscribe(self, topic: str):
    self.client.subscribe(topic)

  def loop_forever(self):
    self.client.loop_forever()

  def disconnect(self):
    self.client.disconnect()
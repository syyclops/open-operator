import paho.mqtt.client as paho
from paho import mqtt
import os
import atexit

class MQTTClient:
  """
  MQTTClient is a simple wrapper around the paho.mqtt.client class. It is used to connect to an MQTT broker and subscribe to a topic.
  """
  def __init__(self, host: str | None = None, username: str | None = None, password: str | None = None, port=8883, topic="#"):
    if host is None:
      host = os.environ['MQTT_BROKER_ADDRESS']
    if username is None:
      username = os.environ['MQTT_USERNAME']
    if password is None:
      password = os.environ['MQTT_PASSWORD']
    self.client = paho.Client(paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5, clean_session=True)
    self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    self.client.username_pw_set(username, password)
    self.client.on_connect = self.on_connect
    # self.client.on_message = on_message
    self.host = host
    self.port = port
    self.topic = topic
    atexit.register(self.stop)

  def on_connect(self, client, userdata, flags, rc, properties=None):
    print("Connected to MQTT broker with result code "+str(rc))
    client.subscribe(self.topic)

  def start(self):
    self.client.connect(self.host, self.port, 60)
    self.client.loop_forever()

  def stop(self):
    self.client.disconnect()
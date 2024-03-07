import paho.mqtt.client as paho
from paho import mqtt
import atexit

class MQTTClient:
  """
  MQTTClient is a simple wrapper around the paho.mqtt.client class. It is used to connect to an MQTT broker and subscribe to a topic.
  """
  def __init__(self, host: str, username: str, password: str, on_message, port=8883, topic="#"):
    self.client = paho.Client(paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)
    self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    self.client.username_pw_set(username, password)
    self.client.on_connect = self.on_connect
    self.client.on_message = on_message
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
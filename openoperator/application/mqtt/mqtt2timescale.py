from openoperator.infrastructure import MQTTClient, Timescale, Postgres
from openoperator.domain.service.mqtt_service import MQTTService
import atexit
from dotenv import load_dotenv
load_dotenv()

mqtt_client = MQTTClient()
postgres = Postgres()
timescale = Timescale(postgres=postgres)

mqtt_service = MQTTService(mqtt_client, timescale)

mqtt_service.start_message_listener(topic="#")

def on_exit():
  mqtt_service.stop()
  mqtt_client.disconnect()

atexit.register(on_exit)
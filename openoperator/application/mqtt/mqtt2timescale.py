from openoperator.infrastructure import MQTTClient, Timescale, Postgres
from openoperator.domain.service.mqtt_service import MQTTService

mqtt_client = MQTTClient()
postgres = Postgres()
timescale = Timescale(postgres=postgres)

mqtt_service = MQTTService(mqtt_client, timescale)

mqtt_service.start()
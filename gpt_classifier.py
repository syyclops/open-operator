from rdflib import Graph, Namespace
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

client = OpenAI()

prompt = """BRICK SCHEMA EQUIPMENT TYPES:

Equipment
Elevator
Gas Distribution
Relay
Steam Distribution
Water Distribution
Weather Station
Camera
Surveillance Camera
Furniture
Stage Riser
Solar Thermal Collector
PVT Panel
Motor
Variable Frequency Drive
VFD
Fan VFD
Heat Wheel VFD
Pump VFD
Shading Equipment
Automatic Tint Window
Blind
Water Heater
Collection Basin Water Heater
Boiler
Electric Boiler
Natural Gas Boiler
Condensing Natural Gas Boiler
Noncondensing Natural Gas Boiler
Lighting Equipment
Interface
Touchpanel
Switch
Dimmer
Lighting
Luminaire
Luminaire Driver
Safety Equipment
First Aid Kit
AED
Automated External Defibrillator
Emergency Wash Station
Drench Hose
Eye Wash Station
Safety Shower
Security Equipment
Intrusion Detection Equipment
Access Control Equipment
Access Reader
Intercom Equipment
Emergency Phone
Video Intercom
Video Surveillance Equipment
NVR
Network Video Recorder
PV Panel
Fire Safety Equipment
Fire Alarm
Fire Alarm Control Panel
Fire Control Panel
Heat Detector
Smoke Detector
Manual Fire Alarm Activation Equipment
Fire Alarm Manual Call Point
Fire Alarm Pull Station
Valve
Gas Valve
Natural Gas Seismic Shutoff Valve
HVAC Valve
Chilled Water Valve
Condenser Water Valve
Makeup Water Valve
Water Valve
Thermostatic Mixing Valve
Hot Water Valve
Domestic Hot Water Valve
Preheat Hot Water Valve
Electrical Equipment
Breaker Panel
Bus Riser
Disconnect Switch
Inverter
Motor Control Center
PlugStrip
Switchgear
Transformer
Energy Storage
Battery
Meter
Thermal Power Meter
Electrical Meter
Building Electrical Meter
Gas Meter
Building Gas Meter
Water Meter
Building Water Meter
Chilled Water Meter
Building Chilled Water Meter
Hot Water Meter
Building Hot Water Meter
Building Meter
HVAC Equipment
Compressor
Condenser
Cooling Tower
Cooling Valve
Dry Cooler
Economizer
Fume Hood
Humidifier
Space Heater
Steam Valve
Thermostat
Air Handler Unit
Air Handling Unit
CRAH
Cold Deck
Computer Room Air Conditioning
Computer Room Air Handler
HX
Hot Deck
Isolation Valve
Condenser Water Isolation Valve
Pump
Water Pump
Chilled Water Pump
Condenser Water Pump
Hot Water Pump
Bypass Valve
Condenser Water Bypass Valve
Differential Pressure Bypass Valve
CRAC
Standby CRAC
Air Plenum
Return Air Plenum
Discharge Air Plenum
Supply Air Plenum
Underfloor Air Plenum
Chiller
Absorption Chiller
Centrifugal Chiller
Heating Valve
Reheat Valve
Return Heating Valve
Heat Exchanger
Condenser Heat Exchanger
Evaporative Heat Exchanger
Heat Wheel
Coil
Cooling Coil
Chilled Water Coil
Direct Expansion Cooling Coil
Heating Coil
Direct Expansion Heating Coil
Hot Water Coil
Filter
Final Filter
Intake Air Filter
Mixed Air Filter
Pre Filter
Return Air Filter
Damper
Economizer Damper
Exhaust Damper
Mixed Damper
Outside Damper
Relief Damper
Return Damper
AHU
PAU
DOAS
Dedicated Outdoor Air System Unit
Dual Duct Air Handling Unit
MAU
Makeup Air Unit
RTU
Rooftop Unit
DDAHU
Fan
Booster Fan
Ceiling Fan
Cooling Tower Fan
Exhaust Fan
Outside Fan
Relief Fan
Return Fan
Standby Fan
Supply Fan
Transfer Fan
Discharge Fan
Terminal Unit
Constant Air Volume Box
Fan Coil Unit
Induction Unit
CAV
FCU
VAV
Chilled Beam
Active Chilled Beam
Passive Chilled Beam
Variable Air Volume Box
Variable Air Volume Box With Reheat
RVAV
Air Diffuser
Displacement Flow Air Diffuser
Jet Nozzle Air Diffuser
Laminar Flow Air Diffuser
Radiator
Electric Radiator
Electric Baseboard Radiator
Hot Water Radiator
Hot Water Baseboard Radiator
Steam Radiator
Steam Baseboard Radiator
Baseboard Radiator
Radiant Panel
Embedded Surface System Panel
Radiant Ceiling Panel
Thermally Activated Building System Panel
ESS Panel
RC Panel
TABS Panel

You are a system that is given a bacnet device name and you output whats its correct brick schema classification class is. ONLY output the brick class. If the brick class is unknown output N/A.
    
Device name: AHU-1

Brick Class: AHU

Device name:"""

# Define Namespace
BRICK = Namespace("https://brickschema.org/schema/Brick#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
A = RDF['type']

# Load the graph
g = Graph()
g.bind('brick', BRICK)
g.bind('rdf', RDF)
g.parse("data/dunbar/bacnet.ttl", format="turtle")


# Define a SPARQL query for bacnet_Device
query_for_devices = """
PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

SELECT ?device ?device_name
WHERE {
  ?device a bacnet:bacnet_Device ;
          bacnet:device_name ?device_name .
}
"""

# Run the query for devices
for row in g.query(query_for_devices):
    device_uri = row[0]
    device_name = row[1]

    input = prompt + device_name + "\n" + "Brick Class: "

    response = client.completions.create(
      model="gpt-3.5-turbo-instruct",
      prompt=input,
      temperature=0
    )

    # Get the response
    response = response.choices[0].text

    # Remove any whitespace at the beginning or end
    response = response.strip()

    if response != "N/A":
        print(device_name + " is a " + response)

        # Replace all whitespace with _
        brick_class = BRICK[response.replace(" ", "_")]
        print(brick_class)

        # Add the brick class to the graph
        g.add((device_uri, A, brick_class))

# Save the graph
g.serialize("data/dunbar/brick.ttl", format="turtle")

    
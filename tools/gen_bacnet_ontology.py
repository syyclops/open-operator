from rdflib import Graph, Namespace
from rdflib.namespace import RDF, OWL
from rdflib.namespace import RDFS

# Define the BACnet namespace
BACNET = Namespace("http://data.ashrae.org/bacnet#")

# Create a new graph
g = Graph()

# Define the classes
bacnet_Device = BACNET.Device  # Classes typically have capitalized names
bacnet_Point = BACNET.Point

# Add the classes to the graph
g.add((bacnet_Device, RDF.type, OWL.Class))
g.add((bacnet_Point, RDF.type, OWL.Class))

# Define properties for bacnet_Device
device_address = BACNET.device_address
device_description = BACNET.device_description
device_id = BACNET.device_id
device_name = BACNET.device_name
object_description = BACNET.object_description
object_index = BACNET.object_index
object_name = BACNET.object_name
object_units = BACNET.object_units
present_value = BACNET.present_value
raw_description = BACNET.raw_description

# Add properties for bacnet_Device to the graph as DatatypeProperty
g.add((device_address, RDF.type, OWL.DatatypeProperty))
g.add((device_description, RDF.type, OWL.DatatypeProperty))
g.add((device_id, RDF.type, OWL.DatatypeProperty))
g.add((device_name, RDF.type, OWL.DatatypeProperty))
g.add((object_description, RDF.type, OWL.DatatypeProperty))
g.add((object_index, RDF.type, OWL.DatatypeProperty))
g.add((object_name, RDF.type, OWL.DatatypeProperty))
g.add((object_units, RDF.type, OWL.DatatypeProperty))
g.add((present_value, RDF.type, OWL.DatatypeProperty))
g.add((raw_description, RDF.type, OWL.DatatypeProperty))

# Define properties for bacnet_Point
point_device_address = BACNET.device_address  # Assuming same as device_address for simplicity
object_name = BACNET.object_name
object_units = BACNET.object_units
device_id = BACNET.device_id 
present_value = BACNET.present_value
device_name = BACNET.device_name
object_description = BACNET.object_description

# Add properties for bacnet_Point to the graph as DatatypeProperty
g.add((point_device_address, RDF.type, OWL.DatatypeProperty))
g.add((object_name, RDF.type, OWL.DatatypeProperty))
g.add((object_units, RDF.type, OWL.DatatypeProperty))
g.add((device_id, RDF.type, OWL.DatatypeProperty))
g.add((present_value, RDF.type, OWL.DatatypeProperty))
g.add((device_name, RDF.type, OWL.DatatypeProperty))
g.add((object_description, RDF.type, OWL.DatatypeProperty))

# Define relationships (using ObjectProperty to relate points to devices)
objectOf = BACNET.objectOf
g.add((objectOf, RDF.type, OWL.ObjectProperty))

# Set the domain and range of the objectOf property
g.add((objectOf, RDFS.domain, bacnet_Point))
g.add((objectOf, RDFS.range, bacnet_Device))

# Serialize the graph in Turtle format
g.serialize('../ontology_files/Bacnet_ontology.ttl', format='turtle')

from rdflib import Graph, URIRef, Literal, RDF, Namespace
from rdflib.namespace import RDFS, XSD

BRICK = Namespace("https://brickschema.org/schema/Brick#")
EXAMPLE = Namespace("https://example.com/building#")
A = RDF.type

# This function creates an equipment node in the graph with the given name and type
def create_equipment(g, equipment_name, equipment_type):
    g.add((
        EXAMPLE[equipment_name],
        A,
        equipment_type
    ))

# This function creates a point node in the graph with the given name and type
def create_point(g, point_name, point_type):
    g.add((
        EXAMPLE[point_name],
        A,
        point_type
    ))

# This function creates a relationship between two nodes in the graph
def create_relationship(g, source, relationship, target):
    g.add((
        EXAMPLE[source],
        relationship,
        EXAMPLE[target]
    ))

# Create AHU template
def create_ahu():
    g = Graph()
    g.bind('brick', BRICK)
    g.bind('ex', EXAMPLE)

    # Define Equipment
    create_equipment(g, 'ahu1', BRICK.AHU)
    create_equipment(g, 'supplyFan1', BRICK.Supply_Fan)
    create_equipment(g, 'returnFan1', BRICK.Return_Fan)
    create_equipment(g, 'heatingCoil1', BRICK.Heating_Coil)
    create_equipment(g, 'coolingCoil1', BRICK.Cooling_Coil)
    create_equipment(g, 'filter1', BRICK.Filter)


    # Define Points
    create_point(g, 'tempSensor1', BRICK.Temperature_Sensor)

    # Define Relationships
    create_relationship(g, 'ahu1', BRICK.hasPart, 'supplyFan1')
    create_relationship(g, 'ahu1', BRICK.hasPart, 'returnFan1')
    create_relationship(g, 'ahu1', BRICK.hasPart, 'heatingCoil1')
    create_relationship(g, 'ahu1', BRICK.hasPart, 'coolingCoil1')
    create_relationship(g, 'ahu1', BRICK.hasPart, 'filter1')
    create_relationship(g, 'ahu1', BRICK.hasPoint, 'tempSensor1')

    # TODO: Define Units


    g.serialize('ahu_template.ttl', format='turtle')

def main():
    create_ahu()

if __name__ == '__main__':
    main()
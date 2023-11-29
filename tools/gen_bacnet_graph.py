import argparse
import json
from rdflib import Graph, Namespace, Literal, BNode, URIRef
import re

# Define namespaces for the graph
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SYYCLOPS = Namespace('https://syyclops.com/')
BACNET = Namespace("http://data.ashrae.org/bacnet/#")
A = RDF['type']

def load_bacnet_json(path):
    """
    Load BACnet JSON file
    :param path: path to the BACnet JSON file
    :return: list of JSON objects
    """
    assert path.endswith('.json'), 'File must be a JSON file'

    # Load JSON file
    f = open(path)
    data = json.load(f)

    return data

# Function to create a URI from a string
def create_uri(name: str) -> str:
    # function to transform the name string into a URI
    return re.sub(r'[^a-zA-Z0-9]', '', str(name).lower())

def main():
    # Create arguments
    parser = argparse.ArgumentParser(description='Generate Brick Graph from BACnet JSON file')
    parser.add_argument('--path', type=str, help='path to the BACnet json file')
    parser.add_argument('--customerName', type=str, help='name of the customer')
    parser.add_argument('--buildingName', type=str, help='name of the building')
    parser.add_argument('--output', type=str, help='path to the output file')
    parser.parse_args()
    path = parser.parse_args().path
    customer_name = parser.parse_args().customerName
    building_name = parser.parse_args().buildingName
    output = parser.parse_args().output

    assert path, 'Path to BACnet JSON file must be specified'
    assert customer_name, 'Customer name must be specified'
    assert building_name, 'Building name must be specified'
    assert output, 'Output file must be specified'

    facility_uri = SYYCLOPS[customer_name + '/' + building_name]

    # Load JSON file
    data = load_bacnet_json(path)

    # Create Brick Graph
    g = Graph()
    g.bind('bacnet', BACNET)
    g.bind('rdf', RDF)
    g.bind('syyclops', SYYCLOPS)

    # Loop through the bacnet json file
    for item in data:
        if item['Bacnet Data'] == None:
            continue
        if item['Bacnet Data'] == "{}":
            continue
        bacnet_data = json.loads(item['Bacnet Data'])[0]

        # Check if the necessary keys are in bacnet_data
        if not all(key in bacnet_data for key in ['device_address', 'device_id', 'device_name']):
            print("Missing necessary key in bacnet_data, skipping this item.")
            continue

        device_uri = facility_uri + '/device/' + bacnet_data['device_address'] + "-" + bacnet_data['device_id'] + '/' + create_uri(bacnet_data['device_name'])
        # Check if its a bacnet device or a bacnet object
        if bacnet_data['object_type'] == "device":
           # Create the bacnet device and add it to the graph
            g.add((device_uri, A, BACNET.bacnet_Device))

            # Go through all the bacnet data and add it to the graph
            for key, value in bacnet_data.items():
                if key == "object_type":
                    continue
                g.add((device_uri, BACNET[key], Literal(str(value))))
        else:
            # Create the bacnet point and add it to the graph
            point_uri = device_uri + '/point/' + bacnet_data['object_type'] + "/" + create_uri(bacnet_data['object_name']) + "/" + bacnet_data['object_index']
            g.add((point_uri, A, BACNET.bacnet_Point))

            # Go through all the bacnet data and add it to the graph
            for key, value in bacnet_data.items():
                if key == "object_type":
                    continue
                g.add((point_uri, BACNET[key], Literal(str(value))))

            # Create relationship between the device and the point
            g.add((point_uri, BACNET.objectOf, device_uri))

    # Serialize the graph
    g.serialize(output, format='turtle')

if __name__ == '__main__':
    main()

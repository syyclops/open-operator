import pandas as pd 
from brickschema import Graph
from brickschema.namespaces import BRICK, A
from rdflib import URIRef, Namespace, RDFS, Literal
import urllib.parse
import argparse
from pyshacl import validate
from enum import Enum
import os

def main():
    dict_of_dfs = pd.read_excel("files/cobie/SampleCOBieSpreadsheet.xlsx", sheet_name=["Facility", "Floor", "Space", "Zone", "Type", "Component", "System"])

    g = Graph()
    BLDG = Namespace("https://app.syyclops.com#pn0001")
    COBIE = Namespace("https://cobie.org/schema/CObie#")
    g.bind("bldg", BLDG)
    g.bind("brick", BRICK)
    g.bind("cobie", COBIE)

    building_df = dict_of_dfs["Facility"]
    building_uri = building_df["ExternalSiteIdentifier"][0]
    building_name = building_df["Name"][0]

    g.add((BLDG[building_uri], A, COBIE.Facility))
    g.add((BLDG[building_uri], RDFS.label, Literal(building_name)))

    ## Create Floors
    for floor in dict_of_dfs["Floor"].iterrows():
        floor_uri = floor[1]["ExtIdentifier"]
        floor_name = floor[1]["Name"]

        g.add((BLDG[floor_uri], A, COBIE.Floor))
        g.add((BLDG[floor_uri], RDFS.label, Literal(floor_name)))
        g.add((BLDG[building_uri], BRICK.hasPart, BLDG[floor_uri]))

    ## Create Spaces
    for space in dict_of_dfs["Space"].iterrows():
        # if space[1]["FloorName"] == floor_name:
        space_uri = space[1]["ExtIdentifier"]
        space_name = space[1]["Name"]

        floor_index = dict_of_dfs["Floor"]["Name"].tolist().index(space[1]["FloorName"])
        floor = dict_of_dfs["Floor"].iloc[floor_index]
        floor_uri = floor["ExtIdentifier"]

        g.add((BLDG[space_uri], A, COBIE.Space))
        g.add((BLDG[space_uri], RDFS.label, Literal(space_name)))
        g.add((BLDG[floor_uri], BRICK.hasPart, BLDG[space_uri]))


    # Create Zones and assign rooms to those zones
    for zone in dict_of_dfs["Zone"].iterrows():
        zone_uri = zone[1]["ExtIdentifier"]
        zone_name = zone[1]["Name"]

        g.add((BLDG[zone_uri], A, COBIE.Zone))
        g.add((BLDG[zone_uri], RDFS.label, Literal(zone_name)))

        # Get the space that is in this zone
        space_name = zone[1]["SpaceNames"]
        space_index = dict_of_dfs["Space"]["Name"].tolist().index(space_name)
        space = dict_of_dfs["Space"].iloc[space_index]
        g.add((BLDG[zone_uri], COBIE.spaceNames, BLDG[space["ExtIdentifier"]]))

    # Create Types
    for type in dict_of_dfs["Type"].iterrows():
        type_uri = type[1]["ExtIdentifier"]

        g.add((BLDG[type_uri], A, COBIE.Type))
        g.add((BLDG[type_uri], RDFS.label, Literal(type[1]["Name"])))
        g.add((BLDG[type_uri], COBIE.Category, Literal(type[1]["Category"])))
        g.add((BLDG[type_uri], COBIE.Manufacturer, Literal(type[1]["Manufacturer"])))
        g.add((BLDG[type_uri], COBIE.ModelNumber, Literal(type[1]["ModelNumber"])))

    # Create components
    #   Give them a type
    #   Assign them to a space
    for component in dict_of_dfs["Component"].iterrows():
        component_uri = component[1]["ExtIdentifier"]
        component_name = component[1]["Name"]
        component_type_name = component[1]["TypeName"]

        g.add((BLDG[component_uri], A, COBIE.Component))
        g.add((BLDG[component_uri], RDFS.label, Literal(component_name)))
        g.add((BLDG[component_uri], COBIE.SerialNumber, Literal(component[1]["SerialNumber"])))

        # Get the Type for component
        type_index = dict_of_dfs["Type"]["Name"].tolist().index(component_type_name)
        type = dict_of_dfs["Type"].iloc[type_index]
        type_uri = type["ExtIdentifier"]
        g.add((BLDG[component_uri], COBIE.typeName, BLDG[type_uri]))

        # Find the Space component is in
        component_space_names = component[1]["Space"].split(",")
        for space_name in component_space_names:
            space_name = space_name.strip()
            space_index = dict_of_dfs["Space"]["Name"].tolist().index(space_name)
            space = dict_of_dfs["Space"].iloc[space_index]
            space_uri = space["ExtIdentifier"]
            g.add((BLDG[component_uri], COBIE.spaceNames, BLDG[space_uri]))

    # Create Systems
    for system in dict_of_dfs["System"].iterrows():
        system_uri = system[1]["ExtIdentifier"]

        g.add((BLDG[system_uri], A, COBIE.System))
        g.add((BLDG[system_uri], RDFS.label, Literal(system[1]["Name"])))
        g.add((BLDG[system_uri], COBIE.Category, Literal(system[1]["Category"])))

        component_index = dict_of_dfs["Component"]["Name"].tolist().index(system[1]["ComponentNames"])
        component = dict_of_dfs["Component"].iloc[component_index]
        component_uri = component["ExtIdentifier"]

        g.add((BLDG[component_uri], COBIE.extSystem, BLDG[system_uri]))


    valid, _, report = validate(g)
    print(f"Graph is valid? {valid}")
    print(report)
    g.serialize("./files/output_ttl/out.ttl", format="turtle")



if __name__ == "__main__":
    main()
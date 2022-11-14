from brickschema import Graph
import ifcopenshell
import ifcopenshell.util.element as Element
from brickschema.namespaces import BRICK, A
from rdflib import URIRef, Namespace, RDFS, Literal
import urllib.parse
import argparse
from pyshacl import validate
from enum import Enum
import os

from azure.storage.blob.aio import BlobClient
import asyncio
import requests


class Ifc_ModelType(Enum):
    A = "Architectural"
    M = "Mechanical"
    E = "Electrical"
    P = "Plumbing"

# Conversion of IFC types to Brick Types
# The IFC types only go into real detail about the Architectural assets
def ifc_type_2_brick_arch(element):
    ifc_type = element.get_info()["type"]
    type = None
    if ifc_type == "IfcWall":
        type = BRICK.Wall
    elif ifc_type == "IfcDoor":
        type = BRICK.Door
    elif ifc_type == "IfcRailing":
        type = BRICK.Railing
    elif ifc_type == "IfcColumn":
        type = BRICK.Column
    elif ifc_type == "IfcSlab":
        type = BRICK.Slab
    elif ifc_type == "IfcWallStandardCase":
        type = BRICK.Wall
    elif ifc_type == "IfcBeam":
        type = BRICK.Beam
    elif ifc_type == "IfcStair":
        type = BRICK.Stair
    elif ifc_type == "IfcWindow":
        type = BRICK.Window
    elif ifc_type == "IfcStairFlight":
        type = BRICK.StairFlight
    elif ifc_type == "IfcRoof":
        type = BRICK.Roof
    else:
        type = BRICK.Equipment

    # Custom Brick Pset data placed in by BIM team
    if "Custom_Pset" in Element.get_psets(element, psets_only=True).keys():
        brick_pset = Element.get_psets(element, psets_only=True)["Custom_Pset"]
        if "brick_type" in brick_pset.keys():
            type = BRICK[brick_pset["brick_type"]]
        
    return type


# Add Dimensions Pset to the element
def add_dimensions_to_element(BLDG, g, uri, element): 
    if "Dimensions" in Element.get_psets(element, psets_only=True).keys():
        dimensions = Element.get_psets(element, psets_only=True)["Dimensions"]
        if "Area" in dimensions.keys():
            g.add((BLDG[uri], BRICK.grossArea, Literal(round(dimensions["Area"], 2))))
        if "Length" in dimensions.keys():
            g.add((BLDG[uri], BRICK.length, Literal(round(dimensions["Length"], 2))))
        if "Volume" in dimensions.keys():
            g.add((BLDG[uri], BRICK.volume, Literal(round(dimensions["Volume"], 2))))


# Adds Identity Data Pset to the element
def add_identity_data_to_element(BLDG, g, uri, element):
    if "Identity Data" in Element.get_psets(element, psets_only=True).keys():
        data = Element.get_psets(element, psets_only=True)["Identity Data"]
        if "Model" in data.keys():
            g.add(
                (
                    BLDG[uri],
                    BRICK.modelNo,
                    Literal(data["Model"]),
                )
            )
        if "Manufacturer" in data.keys():
            g.add(
                (
                    BLDG[uri],
                    BRICK.manufacturer,
                    Literal(data["Manufacturer"]),
                )
            )
        if "Type Name" in data.keys():
            g.add(
                (
                    BLDG[uri],
                    BRICK.typeName,
                    Literal(data["Type Name"].replace("'", "").replace("\"", "")),
                )
            )


# Create a brick element from a IFC element
# Get its brick type
# Add Name and external id
# Add the dimensions and identity data
def create_element(BLDG, g, element_uri, element, discipline):
    brick_type = ifc_type_2_brick_arch(element)
    g.add((BLDG[element_uri], A, brick_type))
    g.add((BLDG[element_uri], A, BRICK[discipline]))
    g.add(
        (
            BLDG[element_uri],
            RDFS.label,
            Literal(element.Name.replace('"', "").replace("'", "")),
        )
    )
    g.add(
        (
            BLDG[element_uri],
            BRICK.externalId,
            Literal(element.GlobalId),
        )
    )
    add_dimensions_to_element(BLDG, g, element_uri, element)
    add_identity_data_to_element(BLDG, g, element_uri, element)


# Function to Load all IFC files 
#   @params: ifc_files_paths
#       - array of files paths to ifc file locations
#       - array of discipline names that corresponds with the array of file paths
#               Used to describle the discipline of the provided file path
#   @returns
#       - models array that contains the ifc project, site, building, ifc file, and discipline name
def load_ifc_files(ifc_file_paths, disciplines):
    models = []
    i = 0
    for file_path in ifc_file_paths:
        if os.path.exists(file_path):
            ifc = ifcopenshell.open(file_path)
            project = ifc.by_type("IfcProject")[0]
            site = project.IsDecomposedBy[0].RelatedObjects[0]
            building = site.IsDecomposedBy[0].RelatedObjects[0]

            models.append({"project": project, "site": site, "building": building, "ifc": ifc, "discipline": disciplines[i]})
            print('Loaded model: ' + disciplines[i] + ".")
        else: 
            print("Unable to load model: " + disciplines[i] + ". Not a valid path to file.")
        i += 1

    return models


async def upload_file():
    # f = open("./files/brick_models/out.ttl", "rb")

    blob = BlobClient.from_connection_string(conn_str="BlobEndpoint=https://syymarketingstoracc.blob.core.windows.net/;QueueEndpoint=https://syymarketingstoracc.queue.core.windows.net/;FileEndpoint=https://syymarketingstoracc.file.core.windows.net/;TableEndpoint=https://syymarketingstoracc.table.core.windows.net/;SharedAccessSignature=sv=2021-06-08&ss=bfqt&srt=sco&sp=rwdlacupiyx&se=2022-11-15T00:47:10Z&st=2022-11-14T16:47:10Z&spr=https,http&sig=aWozYOtZNLuD1tdRdxNU0cdct7jKzG9g7SuYeE7Aw9o%3D", container_name="test", blob_name="test.ttl")

    with open("./files/brick_models/out.ttl", "rb") as data:
        await blob.upload_blob(data, overwrite=True)
        await blob.close()
    
    print("https://syymarketingstoracc.blob.core.windows.net/test/test.ttl")

    r = requests.post("http://127.0.0.1:3000/api/v1/ontology/uploadRdfFile", {"url": "https://syymarketingstoracc.blob.core.windows.net/test/test.ttl"})
    print(r.status_code)
    print(r.json())



async def main():
    # Initalize program command line arguments 
    #   IFC Files by disciplines
    #   Building URI and Name
    #   Output Turtle file path
    parser = argparse.ArgumentParser()
    parser.add_argument("--archIfc", help="path to architectural ifc file", default="./files/ifc/arch.ifc")
    parser.add_argument("--mechIfc", help="path to mechanical ifc file", default="./files/ifc/mech.ifc")
    parser.add_argument("--elecIfc", help="path to electrical ifc file", default="./files/ifc/elec.ifc")
    parser.add_argument("--plumIfc", help="path to plumbing ifc file", default="./files/ifc/plum.ifc")
    parser.add_argument("--buildingUri")
    parser.add_argument("--buildingName")
    parser.add_argument("--out", help="Outfile .ttl file path", default="./files/brick_models/out.ttl")
    parser.add_argument("--namespace", default="https://app.syyclops.com/ontology#")

    args = parser.parse_args()

    # Make sure building uri and name are provided
    assert args.buildingUri
    assert args.buildingName
    building_uri = args.buildingUri
    building_name = args.buildingName

    # Load all of the ifc files
    models = load_ifc_files([args.archIfc, args.mechIfc, args.elecIfc, args.plumIfc], ["Architectural", "Mechanical", "Electrical", "Plumbing"])
    
    # Initalize RDF graph 
    g = Graph()
    BLDG = Namespace(args.namespace)

    # Loop through models to update the graph
    for model in models:
        # Create a Building
        g.add((BLDG[building_uri], A, BRICK.Building))
        g.add((BLDG[building_uri], RDFS.label, Literal(building_name)))
        # Building location
        g.add((BLDG[building_uri], BRICK.latitude, Literal(model["site"].RefLatitude)))
        g.add((BLDG[building_uri], BRICK.Longitude, Literal(model["site"].RefLongitude)))
        g.add(
            (
                BLDG[building_uri],
                BRICK.elevation,
                Literal(model["site"].RefElevation),
            )
        )
        # Add model global id to the building
        g.add((BLDG[building_uri], BRICK[model["discipline"] + "URN"], Literal(model["building"].GlobalId)))

        # Create the Floors of the Building
        stories = model["building"].IsDecomposedBy[0].RelatedObjects
        for story in stories:
            story_uri = story.GlobalId
            g.add((BLDG[story_uri], A, BRICK.Floor))
            g.add((BLDG[building_uri], BRICK.hasPart, BLDG[story_uri])) # Building hasPart Floor
            g.add((BLDG[story_uri], RDFS.label, Literal(story.Name))) # Floor has label

            # Create the rooms
            if story.IsDecomposedBy:
                rooms = story.IsDecomposedBy[0].RelatedObjects
                for room in rooms:
                    room_name = room.LongName + " " + room.Name
                    room_uri = room.GlobalId
                    g.add((BLDG[room_uri], A, BRICK.Room))
                    g.add((BLDG[story_uri], BRICK.hasPart, BLDG[room_uri])) # Floor hasPart Room
                    g.add((BLDG[room_uri], RDFS.label, Literal(room_name))) # Room has label
                    g.add((BLDG[building_uri], BRICK.hasPart, BLDG[room_uri])) # Building hasPart Room
                    add_dimensions_to_element(BLDG, g, room_uri, room)
                    g.add(
                        (
                            BLDG[room_uri],
                            BRICK.externalId,
                            Literal(room.GlobalId),
                        )
                    )
                    
                    # Create assets inside a room
                    if room.ContainsElements:
                        elements_in_room = room.ContainsElements[0].RelatedElements
                        for element in elements_in_room:
                            element_uri = element.GlobalId

                            create_element(BLDG, g, element_uri, element, model["discipline"])
                            g.add((BLDG[room_uri], BRICK.hasPart, BLDG[element_uri])) # room hasPart element
                            g.add((BLDG[building_uri], BRICK.hasPart, BLDG[element_uri])) # building hasPart element

            # Create Assets that are apart of the Floors
            if story.ContainsElements:
                elements_on_floor = story.ContainsElements[0].RelatedElements
                for element in elements_on_floor:
                    element_uri = element.GlobalId

                    create_element(BLDG, g, element_uri, element, model["discipline"])
                    g.add((BLDG[story_uri], BRICK.hasPart, BLDG[element_uri])) # Floor hasPart elemenet
                    g.add((BLDG[building_uri], BRICK.hasPart, BLDG[element_uri])) # Building hasPart element

        # Create Systems
        # First create the system node then assign all elements that make up the system
        systems = model["ifc"].by_type("IfcSystem")
        if systems:
            for system in systems:
                system_uri = system.GlobalId
                g.add((BLDG[system_uri], A, BRICK.System))
                g.add((BLDG[system_uri], RDFS.label, Literal(system.Name))) # System has label
                g.add(
                    (
                        BLDG[system_uri],
                        BRICK.externalId,
                        Literal(system.GlobalId),
                    )
                )
                g.add((BLDG[building_uri], BRICK.hasPart, BLDG[system_uri])) # Building hasPart System

                for element in system.IsGroupedBy[0].RelatedObjects:
                    element_uri = element.GlobalId
                    g.add((BLDG[element_uri], BRICK.isPartOf, BLDG[system_uri])) # element isPartOf System

        # Create HVAC Zones
        zones = model["ifc"].by_type("IfcZone")
        if zones:
            for zone in zones:
                zone_uri = zone.GlobalId
                g.add((BLDG[zone_uri], A, BRICK.HVAC_Zone)) 
                g.add((BLDG[zone_uri], RDFS.label, Literal(zone.Name.split(":")[0]))) # Zone has label
                g.add((BLDG[building_uri], BRICK.hasPart, BLDG[zone_uri])) # Building hasPart Zone

                for element in zone.IsGroupedBy[0].RelatedObjects:
                    # Get All Rooms that are apart of this Zone
                    if element.is_a("IfcSpace"):
                        space_uri = element.GlobalId
                        g.add((BLDG[space_uri], BRICK.isPartOf, BLDG[zone_uri])) # Room isPartOf Zone

        # Make sure all ifc building elements are in graph
        elements = model["ifc"].by_type("IfcBuildingElement")
        for element in elements:
            element_uri = element.GlobalId
            create_element(BLDG, g, element_uri, element, model["discipline"])
            g.add((BLDG[building_uri], BRICK.hasPart, BLDG[element_uri])) # Building hasPart element
    
    valid, _, report = validate(g)
    print(f"Graph is valid? {valid}")
    print(report)
    g.serialize(args.out, format="turtle")

    # Upload to Blob storage
    await upload_file()

if __name__ == "__main__":
    asyncio.run(main())
    
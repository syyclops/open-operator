from typing import Union
from fastapi import FastAPI, File, UploadFile
import aiofiles
from brickschema import Graph
import ifcopenshell
import ifcopenshell.util.element as Element
from brickschema.namespaces import BRICK, A
from rdflib import URIRef, Namespace, RDFS, Literal
import urllib.parse
import argparse
from pyshacl import validate
from enum import Enum
from enum import Enum

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}






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
def create_element(BLDG, g, element_uri, element):
    brick_type = ifc_type_2_brick_arch(element)
    g.add((BLDG[element_uri], A, brick_type))
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


def load_ifc_file(ifc_file_path):

    ifc = ifcopenshell.open(ifc_file_path)
    project = ifc.by_type("IfcProject")[0]
    site = project.IsDecomposedBy[0].RelatedObjects[0]
    building = site.IsDecomposedBy[0].RelatedObjects[0]
    return project, site, building, ifc


@app.post("/ifcToBrick")
async def ifc_to_brick_model(file: UploadFile):
    # Save file to disk 
    file_location = f'files/{file.filename}'
    async with aiofiles.open(file_location, 'wb') as out_file:
        content = await file.read()  # async read
        await out_file.write(content)  # async write

    
    ifc = ifcopenshell.open(file_location)
    project = ifc.by_type("IfcProject")[0]
    site = project.IsDecomposedBy[0].RelatedObjects[0]
    building = site.IsDecomposedBy[0].RelatedObjects[0]


    g = Graph()
    BLDG = Namespace("https://app.syyclops.com/ontology#")

    # Create a Building
    building_uri = "setty_us"
    g.add((BLDG[building_uri], A, BRICK.Building))
    g.add((BLDG[building_uri], RDFS.label, Literal("Setty US")))
    # Building location
    g.add((BLDG[building_uri], BRICK.latitude, Literal(site.RefLatitude)))
    g.add((BLDG[building_uri], BRICK.Longitude, Literal(site.RefLongitude)))
    g.add(
        (
            BLDG[building_uri],
            BRICK.elevation,
            Literal(site.RefElevation),
        )
    )

    # Create the Floors of the Building
    stories = building.IsDecomposedBy[0].RelatedObjects
    for story in stories:
        story_uri = story.Name.replace(" ", "_")
        g.add((BLDG[story_uri], A, BRICK.Floor))
        g.add((BLDG[building_uri], BRICK.hasPart, BLDG[story_uri]))
        g.add((BLDG[story_uri], RDFS.label, Literal(story.Name)))

        # Create the rooms
        if story.IsDecomposedBy:
            rooms = story.IsDecomposedBy[0].RelatedObjects
            for room in rooms:
                room_name = room.LongName + " " + room.Name
                room_uri = room.GlobalId
                g.add((BLDG[room_uri], A, BRICK.Room))
                g.add((BLDG[story_uri], BRICK.hasPart, BLDG[room_uri]))
                g.add((BLDG[room_uri], RDFS.label, Literal(room_name)))
                add_dimensions_to_element(BLDG, g, room_uri, room)
                g.add(
                    (
                        BLDG[room_uri],
                        BRICK.externalId,
                        Literal(room.GlobalId),
                    )
                )

                # Building rel
                g.add((BLDG[building_uri], BRICK.hasPart, BLDG[room_uri]))

                # Create assets inside a room
                if room.ContainsElements:
                    elements_in_room = room.ContainsElements[0].RelatedElements
                    for element in elements_in_room:
                        element_uri = element.GlobalId

                        create_element(BLDG, g, element_uri, element)
                        g.add((BLDG[room_uri], BRICK.hasPart, BLDG[element_uri]))

                        # Building rel
                        g.add((BLDG[building_uri], BRICK.hasPart, BLDG[element_uri]))

        # Create Assets that are apart of the Floors
        if story.ContainsElements:
            elements_on_floor = story.ContainsElements[0].RelatedElements
            for element in elements_on_floor:
                element_uri = element.GlobalId

                create_element(BLDG, g, element_uri, element)
                g.add((BLDG[story_uri], BRICK.hasPart, BLDG[element_uri]))

                # Building rel
                g.add((BLDG[building_uri], BRICK.hasPart, BLDG[element_uri]))

    # Create Systems
    # First create the system node then assign all elements that make up the system
    systems = ifc.by_type("IfcSystem")
    if systems:
        for system in systems:
            system_uri = system.GlobalId
            g.add((BLDG[system_uri], A, BRICK.System))
            g.add((BLDG[system_uri], RDFS.label, Literal(system.Name)))
            g.add(
                (
                    BLDG[system_uri],
                    BRICK.externalId,
                    Literal(system.GlobalId),
                )
            )

            # Building rel
            g.add((BLDG[building_uri], BRICK.hasPart, BLDG[system_uri]))

            for element in system.IsGroupedBy[0].RelatedObjects:
                element_uri = element.GlobalId
                g.add((BLDG[element_uri], BRICK.isPartOf, BLDG[system_uri]))

    # Create HVAC Zones
    zones = ifc.by_type("IfcZone")
    if zones:
        for zone in zones:
            zone_uri = zone.GlobalId
            g.add((BLDG[zone_uri], A, BRICK.HVAC_Zone))
            g.add((BLDG[zone_uri], RDFS.label, Literal(zone.Name.split(":")[0])))

            # Building rel
            g.add((BLDG[building_uri], BRICK.hasPart, BLDG[zone_uri]))

            for element in zone.IsGroupedBy[0].RelatedObjects:
                if element.is_a("IfcSpace"):
                    space_uri = element.GlobalId
                    g.add((BLDG[space_uri], BRICK.isPartOf, BLDG[zone_uri]))

    # Make sure all ifc building elements are in graph
    elements = ifc.by_type("IfcBuildingElement")
    for element in elements:
        element_uri = element.GlobalId

        create_element(BLDG, g, element_uri, element)
        # g.add((BLDG[element_uri], BRICK.hasLocation, BLDG[story_uri]))

        # Building rel
        g.add((BLDG[building_uri], BRICK.hasPart, BLDG[element_uri]))
    


    valid, _, report = validate(g)
    print(f"Graph is valid? {valid}")
    print(report)
    graph = g.serialize("files/out.ttl", format="turtle")
    print(graph)

    
    return {"building": building}

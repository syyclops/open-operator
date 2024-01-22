from brickschema import Graph
g = Graph(load_brick=True)
g.expand("rdfs")

# Sparql query to get all the equipment
q = """
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?equip ?label    
WHERE {
    ?equip rdfs:subClassOf* brick:Equipment .
    ?equip rdfs:label ?label .
}
"""

equipment = []

# Run the query
for row in g.query(q):
    equipment.append(row["label"].toPython())   

# Save to txt file
with open("brick_equipment_list.txt", "w") as f:
    for equip in equipment:
        f.write(equip + "\n")

# Sparql query to get all the Point
q = """
PREFIX brick: <https://brickschema.org/schema/Brick#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?point ?label
WHERE {
    ?point rdfs:subClassOf* brick:Point .
    ?point rdfs:label ?label .
}
"""

points = []

# Run the query
for row in g.query(q):
    points.append(row["label"].toPython())

# Save to txt file as onw string separated by comma
with open("brick_point_list.txt", "w") as f:
    f.write(", ".join(points))

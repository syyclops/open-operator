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
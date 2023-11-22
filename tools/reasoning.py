from brickschema import Graph
g = Graph(load_brick=True)
# load example Brick model
g.load_file("../data/example/soda_brick.ttl", format="ttl")
print(f"Before: {len(g)} triples")
g.expand("rdfs")
print(f"After: {len(g)} triples")
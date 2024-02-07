import os
from neo4j import GraphDatabase

class KnowledgeGraph():
    def __init__(
            self,
            neo4j_uri: str | None = None,
            neo4j_user: str | None = None,
            neo4j_password: str | None = None,        
    ) -> None:
        # Create the neo4j driver
        if neo4j_uri is None:
            neo4j_uri = os.environ['NEO4J_URI']
        if neo4j_user is None:
            neo4j_user = os.environ['NEO4J_USER']
        if neo4j_password is None:
            neo4j_password = os.environ['NEO4J_PASSWORD']
        
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        neo4j_driver.verify_connectivity()
        self.neo4j_driver = neo4j_driver

        namespaces = [
            ("cobie", "http://checksem.u-bourgogne.fr/ontology/cobie24#"),
            ("bacnet", "http://data.ashrae.org/bacnet/#"),
        ]
    
        # Set up the graph
        with self.neo4j_driver.session() as session:
            # Check constraint for unique URIs
            result = session.run("SHOW CONSTRAINTS")
            if "n10s_unique_uri" not in [record['name'] for record in result.data()]:
                session.run("CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE")

            # Check if the graph is already configured
            result = session.run("MATCH (n:`_GraphConfig`) RETURN n")
            if len(result.data()) == 0:
                session.run("call n10s.graphconfig.init({handleVocabUris: 'IGNORE'})")
            
            # Check if the graph has the prefixes we need
            preixes = session.run("call n10s.nsprefixes.list()")
            for prefix, uri in namespaces:
                if prefix not in preixes:
                    session.run(f"call n10s.nsprefixes.add('{prefix}', '{uri}')")

    def create_session(self):
        return self.neo4j_driver.session()
    
    def execute(self, query: str, parameters: dict = {}):
        """
        Execute a Cypher query.
        """
        with self.neo4j_driver.session() as session:
            result = session.run(query, parameters)
            return result.data()
                
    def import_rdf_data(self, url: str, format: str = "Turtle", inline: bool = False):
        """
        Import RDF data into the knowledge graph.
        """
        with self.neo4j_driver.session() as session:
            if inline:
                result = session.run("call n10s.rdf.import.inline('{}', '{}') yield terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo return terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo".format(url, format))
            else:
                query = f'call n10s.rdf.import.fetch("{url}", "{format}") yield terminationStatus, triplesLoaded, triplesParsed, namespaces, extraInfo'
                result = session.run(query)

            termination_status = result.data()[0]['terminationStatus'] 
            if termination_status != "OK":
                raise Exception(f"Error importing RDF data: {result.data()[0]}")
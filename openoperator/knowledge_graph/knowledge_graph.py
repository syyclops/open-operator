from neo4j import Driver
from .cobie.cobie import COBie 

class KnowledgeGraph:
    """
    This class handles everything related to the knowledge graph.
    """
    def __init__(
            self, 
            operator, 
            neo4j_driver: Driver,
    ) -> None:
        self.operator = operator
        self.neo4j_driver = neo4j_driver

        self.cobie = COBie(self)

        with self.neo4j_driver.session() as session:
            # Check if the graph is already configured
            result = session.run("MATCH (n:`_GraphConfig`) RETURN n")
            if len(result.data()) == 0:
                # Configure the graph
                session.run("CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE")
                session.run("call n10s.graphconfig.init()")
            
            # Check if the graph has the prefixes we need
            preixes = session.run("call n10s.nsprefixes.list()")
            if "cobie" not in preixes:
                session.run("call n10s.nsprefixes.add('cobie', 'http://checksem.u-bourgogne.fr/ontology/cobie24#')")
    

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

    

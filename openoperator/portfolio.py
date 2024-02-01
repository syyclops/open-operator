from neo4j import Driver
from .facility import Facility
from neo4j.exceptions import Neo4jError
from .utils import create_uri

class Portfolio:
    def __init__(self, operator, neo4j_driver: Driver, uri: str) -> dict:
        self.operator = operator
        self.neo4j_driver = neo4j_driver
        self.uri = uri
        
    def details(self) -> dict:
        """
        Get portfolio details.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Portfolio {uri: $uri}) RETURN n", uri=self.uri)
            return result.data()[0]['n']

    def list_facilities(self) -> list:
        """
        List all facilities in a portfolio.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Facility)-[:PART_OF]-(p:Portfolio {uri: $uri}) RETURN n", uri=self.uri)
            return [record['n'] for record in result.data()]
    
    def facility(self, facility_uri: str) -> Facility:
        return Facility(portfolio=self, knowledge_graph=self.operator.knowledge_graph, uri=facility_uri, blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader)
        
    def create_facility(self, name: str) -> Facility:
        """
        Create a facility.
        """
        facility_uri = f"{self.uri}/{create_uri(name)}"
        print("here")
        print(self.uri)
        query = """MATCH (p:Portfolio {uri: $portfolio_uri})
                    CREATE (n:Facility:Resource {name: $name, uri: $uri}) 
                    CREATE (n)-[:PART_OF]->(p)
                    RETURN n"""
        with self.neo4j_driver.session() as session:
            try:
                result = session.run(query, name=name, portfolio_uri=self.uri, uri=facility_uri)
                if result.single() is None:
                    raise Exception("Error creating facility")
            except Neo4jError as e:
                raise Exception(f"Error creating facility: {e.message}")        
                
        return Facility(portfolio=self, uri=facility_uri, knowledge_graph=self.operator.knowledge_graph, blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader)
        
    def search_documents(self, query: str, limit: int = 15) -> list:
        """
        Search documents in the portfolio.
        """
        return self.operator.vector_store.similarity_search(query=query, limit=limit, filter={"portfolio_uri": self.uri})
    
from neo4j import Driver
import uuid
from .facility import Facility
from neo4j.exceptions import Neo4jError
from .utils import create_uri

class Portfolio:
    def __init__(self, operator, neo4j_driver: Driver, portfolio_id: str) -> dict:
        self.operator = operator
        self.neo4j_driver = neo4j_driver
        self.id = portfolio_id

        # Fetch portfolio from knowledge graph
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("MATCH (n:Portfolio {id: $portfolio_id}) RETURN n", portfolio_id=self.id)
                self.uri = result.single()['n']['uri']
        except Neo4jError as e:
            raise Exception(f"Error fetching portfolio: {e.message}")
        
    def details(self) -> dict:
        """
        Get portfolio details.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Portfolio {id: $portfolio_id}) RETURN n", portfolio_id=self.id)
            return result.data()[0]['n']

    def list_buildings(self) -> list:
        """
        List all facilities in a portfolio.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Facility)-[:PART_OF]-(p:Portfolio {id: $portfolio_id}) RETURN n", portfolio_id=self.id)
            return [record['n'] for record in result.data()]
    
    def facility(self, facility_id: str) -> Facility:
        return Facility(portfolio=self, knowledge_graph=self.operator.knowledge_graph, facility_id=facility_id, blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader)
        
    def create_facility(self, name: str) -> Facility:
        """
        Create a facility.
        """
        facility_uri = f"{self.uri}/{create_uri(name)}"
        id = uuid.uuid4()
        query = """MATCH (p:Portfolio {id: $portfolio_id})
                    CREATE (n:Facility:Resource {name: $name, id: $id, uri: $uri}) 
                    CREATE (n)-[:PART_OF]->(p)
                    RETURN n"""
        with self.neo4j_driver.session() as session:
            try:
                result = session.run(query, name=name, id=str(id), portfolio_id=self.id, uri=facility_uri)
                if result.single() is None:
                    raise Exception("Error creating facility")
            except Neo4jError as e:
                raise Exception(f"Error creating facility: {e.message}")        
                
        return Facility(portfolio=self, knowledge_graph=self.operator.knowledge_graph, facility_id=str(id), blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader)
        
    def search_documents(self, query: str, limit: int = 15) -> list:
        """
        Search documents in the portfolio.
        """
        return self.operator.vector_store.similarity_search(query=query, limit=limit, filter={"portfolio_id": self.id})
    
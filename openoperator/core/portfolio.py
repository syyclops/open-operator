from neo4j import Driver
import uuid
from .facility import Facility
from urllib.parse import quote
from neo4j.exceptions import Neo4jError
class Portfolio:
    def __init__(self, operator, neo4j_driver: Driver, portfolio_id: str, uri: str) -> dict:
        self.operator = operator
        self.neo4j_driver = neo4j_driver
        self.id = portfolio_id
        self.uri = uri  

    def list_buildings(self) -> list:
        """
        List all facilities in a portfolio.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Facility)-[:PART_OF]-(p:Portfolio {id: $portfolio_id}) RETURN n", portfolio_id=self.id)
            return [record['n'] for record in result.data()]
    
    def facility(self, facility_id: str) -> Facility:
        return Facility(portfolio=self, neo4j_driver=self.neo4j_driver, facility_id=facility_id, blob_store=self.operator.blob_store)
        
    def create_facility(self, name: str) -> Facility:
        """
        Create a facility.
        """
        facility_uri = f"{self.uri}/{quote(name)}"
        id = uuid.uuid4()
        query = """CREATE (n:Facility:Resource {name: $name, id: $id, uri: $uri}) 
                    CREATE (n)-[:PART_OF]->(:Portfolio {id: $portfolio_id})
                    RETURN n"""
        with self.neo4j_driver.session() as session:
            try:
                result = session.run(query, name=name, id=str(id), portfolio_id=self.id, uri=facility_uri)
                result.consume()
            except Neo4jError as e:
                raise Exception(f"Error creating facility: {e.message}")        
                
        return Facility(portfolio=self, neo4j_driver=self.neo4j_driver, facility_id=str(id), blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader, uri=facility_uri)
        
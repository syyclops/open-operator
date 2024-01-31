from neo4j import Driver
import uuid
from .facility import Facility

class Portfolio:
    def __init__(self, operator, neo4j_driver: Driver, portfolio_id: str) -> dict:
        self.operator = operator
        self.neo4j_driver = neo4j_driver
        self.portfolio_id = portfolio_id  

    def list_buildings(self) -> list:
        """
        List all facilities in a portfolio.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Facility)-[:PART_OF]-(p:Portfolio {id: $portfolio_id}) RETURN n", portfolio_id=self.portfolio_id)
            return [record['n'] for record in result.data()]
    
    def facility(self, facility_id: str) -> Facility:
        return Facility(portfolio=self, neo4j_driver=self.neo4j_driver, facility_id=facility_id, blob_store=self.operator.blob_store)
        
    def create_facility(self, name: str) -> Facility:
        """
        Create a facility.
        """
        with self.neo4j_driver.session() as session:
            id = uuid.uuid4()
            query = """CREATE (n:Facility {name: $name, id: $id}) 
                        CREATE (n)-[:PART_OF]->(:Portfolio {id: $portfolio_id})
                        RETURN n"""
            result = session.run(query, name=name, id=str(id), portfolio_id=self.portfolio_id)
            return Facility(portfolio=self, neo4j_driver=self.neo4j_driver, facility_id=str(id), blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader)
        
from neo4j.exceptions import Neo4jError
from ...services.knowledge_graph import KnowledgeGraph
from .facility.facility import Facility
from ...utils import create_uri
from ..user import User
from openoperator.types import DocumentQuery 

class Portfolio:
    """
    A portfolio is a collection of facilities.
    """
    def __init__(self, operator, knowledge_graph: KnowledgeGraph, uri: str, user: User) -> dict:
        self.operator = operator
        self.knowledge_graph = knowledge_graph
        self.uri = uri
        self.user = user
        
    def details(self) -> dict:
        with self.knowledge_graph.create_session() as session:
            result = session.run("MATCH (c:Customer {uri: $uri}) RETURN c", uri=self.uri)
            return result.data()[0]['c']

    def list_facilities(self) -> list:
        try:
            with self.knowledge_graph.create_session() as session:
                result = session.run("""
                                    MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]-(f:Facility)
                                    MATCH (c:Customer {uri: $uri})-[:HAS_FACILITY]-(f)
                                    RETURN f
                                    """, email=self.user.email, uri=self.uri)
                facilities = []
                for record in result.data():
                    facility = record['f']
                    facilities.append({
                        "name": facility['name'],
                        "uri": facility['uri'],
                    })
                return facilities
        except Neo4jError as e:
            raise Exception(f"Error listing facilities: {e.message}")
    
    def facility(self, facility_uri: str) -> Facility:
        return Facility(portfolio=self, knowledge_graph=self.knowledge_graph, uri=facility_uri, blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader)
        
    def create_facility(self, name: str) -> Facility:
        facility_uri = f"{self.uri}/{create_uri(name)}"
        query = """MATCH (p:Customer {uri: $portfolio_uri})
                    MATCH (u:User {email: $email})
                    CREATE (f:Facility:Resource {name: $name, uri: $uri}) 
                    CREATE (p)-[:HAS_FACILITY]->(f)
                    CREATE (u)-[:HAS_ACCESS_TO]->(f)
                    RETURN f"""
        with self.knowledge_graph.create_session() as session:
            try:
                result = session.run(query, name=name, portfolio_uri=self.uri, uri=facility_uri, email=self.user.email)
                if result.single() is None:
                    raise Exception("Error creating facility")
            except Neo4jError as e:
                raise Exception(f"Error creating facility: {e.message}")        
                
        return Facility(portfolio=self, uri=facility_uri, knowledge_graph=self.operator.knowledge_graph, blob_store=self.operator.blob_store, vector_store=self.operator.vector_store, document_loader=self.operator.document_loader)
        
    def search_documents(self, params: DocumentQuery) -> list:
        """
        Search contents of all upload documents to the portfolio. These documents are drawings/plans, O&M manuals, etc.
        """
        query = params.query
        limit = params.limit
        return self.operator.vector_store.similarity_search(query=query, limit=limit, filter={"portfolio_uri": self.uri})
    
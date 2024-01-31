from neo4j import Driver
from ..services.blob_store import BlobStore
from ..services.vector_store import VectorStore
from ..services.document_loader import DocumentLoader
from .cobie.cobie import COBie

class Facility:
    def __init__(self, 
                 portfolio,
                 neo4j_driver: Driver, 
                 facility_id: str, 
                 blob_store: BlobStore,
                 vector_store: VectorStore,
                 document_loader: DocumentLoader,
        ) -> None:
        self.portfolio = portfolio
        self.neo4j_driver = neo4j_driver
        self.facility_id = facility_id
        self.blob_store = blob_store
        self.vector_store = vector_store
        self.document_loader = document_loader

    def list_files(self) -> list:
        """
        List all files in a facility.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:File)-[:PART_OF]-(f:Facility {id: $facility_id}) RETURN n", facility_id=self.facility_id)
            return [record['n'] for record in result.data()]
        
    def upload_document(self, file_content: bytes, file_name: str) -> None:
        """
        Upload a file to the facility.
        """
        file_url = self.blob_store.upload_file(file_content=file_content, file_name=file_name)
        docs = self.document_loader.load(file_content=file_content, file_path=file_name)

        # Add metadata to vector store  
        for doc in docs:
            doc.metadata['portfolio_id'] = self.portfolio.portfolio_id
            doc.metadata['facility_id'] = self.facility_id
            doc.metadata['file_url'] = file_url
        
        self.vector_store.add_documents(docs)

        with self.neo4j_driver.session() as session:
            query = """CREATE (d:Document {name: $name, url: $url})
                        CREATE (d)-[:documentTo]->(:Facility {id: $facility_id})
                        RETURN d"""
            result = session.run(query, name=file_name, url=file_url, facility_id=self.facility_id)

            return result.data()[0]['d']
    
    def search_documents(self, query: str, limit: int = 5) -> list:
        """
        Search documents in the facility.
        """
        return self.vector_store.similarity_search(query=query, limit=limit, filter={"facility_id": self.facility_id})
    
    def upload_spreadsheet(self, file_path: str):
        spreadsheet = COBie(file_path)
        rdf_graph_str = spreadsheet.convert_to_graph(f"https://{self.portfolio.portfolio_id}/")

        return rdf_graph_str
    
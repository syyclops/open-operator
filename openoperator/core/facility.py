from ..services.knowledge_graph import KnowledgeGraph
from ..services.blob_store import BlobStore
from ..services.vector_store import VectorStore
from ..services.document_loader import DocumentLoader
from .cobie.cobie import COBie

class Facility:
    def __init__(self, 
                 portfolio,
                 knowledge_graph: KnowledgeGraph, 
                 facility_id: str, 
                 blob_store: BlobStore,
                 vector_store: VectorStore,
                 document_loader: DocumentLoader,
                 uri: str
        ) -> None:
        self.portfolio = portfolio
        self.knowledge_graph = knowledge_graph
        self.neo4j_driver = knowledge_graph.neo4j_driver
        self.id = facility_id
        self.blob_store = blob_store
        self.vector_store = vector_store
        self.document_loader = document_loader
        self.uri = uri

    def list_files(self) -> list:
        """
        List all files in a facility.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (d:Document)-[:documentTo]-(f:Facility {id: $facility_id}) RETURN d", facility_id=self.id)
            return [record['d'] for record in result.data()]
        
    def upload_document(self, file_content: bytes, file_name: str, file_type: str) -> None:
        """
        Upload a file for a facility.

        1. Upload the file to the blob store
        2. Extract metadata from the file
        3. Add metadata to the vector store
        4. Create a document node in the knowledge graph
        """
        try:
            file_url = self.blob_store.upload_file(file_content=file_content, file_name=file_name, file_type=file_type)
        except Exception as e:
            # Log the error and potentially handle specific cases
            raise Exception(f"Error uploading document to blob storage: {e}")

        try:
            docs = self.document_loader.load(file_content=file_content, file_path=file_name)
        except Exception as e:
            # Handle document loading errors specifically
            raise Exception(f"Error loading document content: {e}")

        try:
            # Add metadata to vector store  
            for doc in docs:
                doc.metadata['portfolio_id'] = self.portfolio.id
                doc.metadata['facility_id'] = self.id
                doc.metadata['file_url'] = file_url
            
            self.vector_store.add_documents(docs)
        except Exception as e:
            # Handle errors related to adding documents to the vector store
            raise Exception(f"Error adding documents to vector store: {e}")

        try:
            with self.neo4j_driver.session() as session:
                query = """CREATE (d:Document {name: $name, url: $url})
                            CREATE (d)-[:documentTo]->(:Facility {id: $facility_id})
                            RETURN d"""
                result = session.run(query, name=file_name, url=file_url, facility_id=self.id)

                return result.data()[0]['d']
        except Exception as e:
            # Handle database errors
            raise Exception(f"Error creating document node in Neo4J: {e}")

    
    def search_documents(self, query: str, limit: int = 5) -> list:
        """
        Search documents in the facility.
        """
        return self.vector_store.similarity_search(query=query, limit=limit, filter={"facility_id": self.id})
    
    def upload_cobie_spreadsheet(self, file_path: str):
        """
        Convert a cobie spreadsheet to rdf graph, upload it to the blob store and import it to the knowledge graph.
        """
        try:
            spreadsheet = COBie(file_path)
            rdf_graph_str = spreadsheet.convert_to_graph(namespace=self.uri)
            url = self.blob_store.upload_file(file_content=rdf_graph_str.encode(), file_name=f"{self.id}_cobie.ttl", file_type="text/turtle")
            self.knowledge_graph.import_rdf_data(url)
        except Exception as e:
            raise Exception(f"Error uploading spreadsheet: {e}")

        return url
    
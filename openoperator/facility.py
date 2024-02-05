from .knowledge_graph import KnowledgeGraph
from  .blob_store.blob_store import BlobStore
from .vector_store.vector_store import VectorStore
from .document_loader.document_loader import DocumentLoader
from .cobie.cobie import COBie
from .bas import BAS

class Facility:
    """
    This class represents a facility. A facility is a building, a collection of buildings, or a collection of assets.

    It is responsible for:
    - Uploading documents to the facility
    - Searching documents in the facility
    - Integration with the COBie knowledge graph
    - Integrating with the Building Automation System (BAS)
    """
    def __init__(self, 
                 portfolio,
                 uri: str,
                 knowledge_graph: KnowledgeGraph, 
                 blob_store: BlobStore,
                 vector_store: VectorStore,
                 document_loader: DocumentLoader
        ) -> None:
        self.portfolio = portfolio
        self.knowledge_graph = knowledge_graph
        self.neo4j_driver = knowledge_graph.neo4j_driver
        self.uri = uri
        self.blob_store = blob_store
        self.vector_store = vector_store
        self.document_loader = document_loader

        self.cobie = COBie(self, self.portfolio.operator.embeddings)
        self.bas = BAS(self, self.portfolio.operator.embeddings)
        
    def details(self) -> dict:
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Facility {uri: $facility_uri}) RETURN n", facility_uri=self.uri)
            return result.data()[0]['n']

    def documents(self) -> list:
        """
        List all the documents in the facility.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (d:Document)-[:documentTo]-(f:Facility {uri: $facility_uri}) RETURN d", facility_uri=self.uri)
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
                doc.metadata['portfolio_uri'] = self.portfolio.uri
                doc.metadata['facility_uri'] = self.uri
                doc.metadata['file_url'] = file_url
            
            self.vector_store.add_documents(docs)
        except Exception as e:
            # Handle errors related to adding documents to the vector store
            raise Exception(f"Error adding documents to vector store: {e}")

        try:
            with self.neo4j_driver.session() as session:
                query = """CREATE (d:Document {name: $name, url: $url})
                            CREATE (d)-[:documentTo]->(:Facility {uri: $facility_uri})
                            RETURN d"""
                result = session.run(query, name=file_name, url=file_url, facility_uri=self.uri)

                return result.data()[0]['d']
        except Exception as e:
            # Handle database errors
            raise Exception(f"Error creating document node in Neo4J: {e}")
    

    def delete_document(self, url):
        """
        Delete a document from the facility. This will remove the document from the blob store, the vector store, and the knowledge graph.
        """
        try:
            with self.neo4j_driver.session() as session:
                query = """MATCH (d:Document {url: $url}) DETACH DELETE d"""
                session.run(query, url=url)
            self.blob_store.delete_file(url)
            self.vector_store.delete_documents(filter={"file_url": url})
        except Exception as e:
            raise Exception(f"Error deleting document: {e}")

    
    def search_documents(self, params: dict):
        """
        Search documents in the facility.
        """
        query = params.get("query")
        limit = params.get("limit", 15)
        return self.vector_store.similarity_search(query=query, limit=limit, filter={"facility_uri": self.uri})
    

    
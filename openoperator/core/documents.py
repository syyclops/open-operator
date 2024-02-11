import fitz
import io
from openoperator.services import BlobStore, DocumentLoader, VectorStore, KnowledgeGraph

class Documents:
    """
    This class handles everything related to documents in a facilty

    Its responsibilities are:
    - Fetch, upload, and delete, search documents
    - Run the extraction process
    """
    def __init__(self, facility, knowledge_graph: KnowledgeGraph, blob_store: BlobStore, document_loader: DocumentLoader, vector_store: VectorStore) -> None:
        self.vector_store = vector_store   
        self.blob_store = blob_store
        self.document_loader = document_loader
        self.facility = facility
        self.knowledge_graph = knowledge_graph

    def list(self):
        """
        List all the documents in the facility.
        """
        with self.knowledge_graph.create_session() as session:
            result = session.run("MATCH (d:Document)-[:documentTo]-(f:Facility {uri: $facility_uri}) RETURN d", facility_uri=self.facility.uri)
            return [record['d'] for record in result.data()]
        
    def upload(self, file_content: bytes, file_name: str, file_type: str) -> None:
        """
        Upload a file for a facility.

        1. Upload the file to the blob store
        2. Create a document node in the knowledge graph with extractionStatus = "pending"
        """
        try:
            thumbnail_url = None
            if file_type == "application/pdf":
                doc = fitz.open("pdf", io.BytesIO(file_content))
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(100/72, 100/72))
                thumbnail_url = self.blob_store.upload_file(file_content=pix.tobytes(), file_name=f"{file_name}_thumbnail.png", file_type="image/png")
            
            file_url = self.blob_store.upload_file(file_content=file_content, file_name=file_name, file_type=file_type)
            
        except Exception as e:
            raise Exception(f"Error uploading document to blob storage: {e}")

        try:
            with self.knowledge_graph.create_session() as session:
                query = """CREATE (d:Document {name: $name, url: $url, extractionStatus: 'pending', thumbnailUrl: $thumbnail_url})
                            CREATE (d)-[:documentTo]->(:Facility {uri: $facility_uri})
                            RETURN d"""
                result = session.run(query, name=file_name, url=file_url, facility_uri=self.facility.uri, thumbnail_url=thumbnail_url)

                return result.data()[0]['d']
        except Exception as e:
            raise Exception(f"Error creating document node in Neo4J: {e}")
        
    def update_extraction_status(self, url, status):
        """
        Update the extraction status of a document in the knowledge graph.
        pending, failed, or success
        """
        try:
            with self.knowledge_graph.create_session() as session:
                query = """MATCH (d:Document {url: $url})
                           SET d.extractionStatus = $status
                           RETURN d"""
                result = session.run(query, url=url, status=status)
                return result.data()[0]['d']
        except Exception as e:
            raise Exception(f"Error updating extraction status: {e}")
        
    def run_extraction_process(self, file_content: bytes, file_name: str, file_url: str) -> None:
        try:
            docs = self.document_loader.load(file_content=file_content, file_path=file_name)
        except Exception as e:
            self.update_extraction_status(file_url, "failed")
            raise Exception(f"Error loading document content: {e}")

        try:
            # Add metadata to vector store  
            for doc in docs:
                doc.metadata['portfolio_uri'] = self.facility.portfolio.uri
                doc.metadata['facility_uri'] = self.facility.uri
                doc.metadata['file_url'] = file_url
            
            self.vector_store.add_documents(docs)
        except Exception as e:
            self.update_extraction_status(file_url, "failed")
            raise Exception(f"Error adding documents to vector store: {e}")
        
        self.update_extraction_status(file_url, "success")
        
    def delete(self, url):
        """
        Delete a document from the facility. This will remove the document from the blob store, the vector store, and the knowledge graph.
        """
        try:
            with self.knowledge_graph.create_session() as session:
                query = """MATCH (d:Document {url: $url}) DETACH DELETE d"""
                session.run(query, url=url)
            self.blob_store.delete_file(url)
            self.vector_store.delete_documents(filter={"file_url": url})
        except Exception as e:
            raise Exception(f"Error deleting document: {e}")

    def search(self, params: dict) -> list:
        """
        Search vector store for documents in the facility
        """
        query = params.get('query')
        limit = params.get('limit') or 15
        file_url = params.get('file_url')
        filter = {"facility_uri": self.facility.uri}
        if file_url:
            filter['file_url'] = file_url
        return self.vector_store.similarity_search(query=query, limit=limit, filter=filter)
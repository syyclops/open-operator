from openoperator.domain.model.document import Document, DocumentQuery, DocumentMetadataChunk
from openoperator.infrastructure import KnowledgeGraph, BlobStore, DocumentLoader, VectorStore
import fitz
import io
from uuid import uuid4
from typing import List, Literal

class DocumentRepository:
  def __init__(self, kg: KnowledgeGraph, blob_store: BlobStore, document_loader: DocumentLoader, vector_store: VectorStore):
    self.kg = kg
    self.blob_store = blob_store
    self.document_loader = document_loader
    self.vector_store = vector_store

  def list(self, facility_uri: str) -> List[Document]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (d:Document)-[:documentTo]-(f:Facility {uri: $facility_uri}) RETURN d", facility_uri=facility_uri)
      data = result.data()
      return [Document(**record['d']) for record in data]
  
  def upload(self, facility_uri: str, file_content: bytes, file_name: str, file_type: str, discipline: Literal['Architectural', 'Plumbing', 'Electrical', 'Mechanical']) -> Document:
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
      raise e

    try:
      with self.kg.create_session() as session:
        doc_uri = f"{facility_uri}/document/{str(uuid4())}"
        query = """CREATE (d:Document:Resource {name: $name, url: $url, extractionStatus: 'pending', thumbnailUrl: $thumbnail_url, uri: $doc_uri, discipline: $discipline})
                    CREATE (d)-[:documentTo]->(:Facility {uri: $facility_uri})
                    RETURN d"""
        result = session.run(query, name=file_name, url=file_url, facility_uri=facility_uri, thumbnail_url=thumbnail_url, doc_uri=doc_uri, discipline=discipline)
        data = result.data()
        if len(data) == 0: raise ValueError("Document not created")
        return Document(extractionStatus="pending", name=file_name, uri=doc_uri, url=file_url, thumbnailUrl=thumbnail_url)
    except Exception as e:
      raise e
    
  def update_extraction_status(self, uri, status):
    """
    Update the extraction status of a document in the knowledge graph.
    pending, failed, or success
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) SET d.extractionStatus = $status RETURN d"
        result = session.run(query, uri=uri, status=status)
        return result.data()[0]['d']
    except Exception as e:
      raise e
        
  def run_extraction_process(self, portfolio_uri: str, facility_uri, file_content: bytes, file_name: str, doc_uri: str, doc_url: str):
    try:
      docs = self.document_loader.load(file_content=file_content, file_path=file_name)
    except Exception as e:
      self.update_extraction_status(doc_uri, "failed")
      raise e

    try:
      # Add metadata to vector store
      for doc in docs:
        doc.metadata['portfolio_uri'] = portfolio_uri
        doc.metadata['facility_uri'] = facility_uri
        doc.metadata['document_uri'] = doc_uri
        doc.metadata['document_url'] = doc_url
    
      self.vector_store.add_documents(docs)
    except Exception as e:
      self.update_extraction_status(doc_uri, "failed")
      raise e
    
    return self.update_extraction_status(doc_uri, "success")
  
  def delete(self, uri):
    """
    Delete a document from the facility. This will remove the document from the blob store, the vector store, and the knowledge graph.
    """
    try:
      with self.kg.create_session() as session:
        query = "MATCH (d:Document {uri: $uri}) WITH d, d.url as url DETACH DELETE d RETURN url"
        result = session.run(query, uri=uri)
        data = result.data()
        if len(data) == 0:
          raise ValueError(f"Document with uri {uri} not found")
      url = data[0]['url']
      self.blob_store.delete_file(url)
      self.vector_store.delete_documents(filter={"document_uri": uri})
    except Exception as e:
      raise e
    
  def search(self, params: DocumentQuery) -> List[DocumentMetadataChunk]:
    """
    Search vector store for documents in the facility
    """
    query = params.query
    limit = params.limit
    query_filter = {"portfolio_uri": params.portfolio_uri}
    if params.facility_uri:
      query_filter = {"facility_uri": params.facility_uri}
    if params.document_uri:
      query_filter['document_uri'] = params.document_uri
    return self.vector_store.similarity_search(query=query, limit=limit, filter=query_filter)
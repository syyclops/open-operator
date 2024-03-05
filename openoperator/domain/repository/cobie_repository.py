from openoperator.infrastructure import KnowledgeGraph, BlobStore
from uuid import uuid4

class COBieRepository:
  def __init__(self, kg: KnowledgeGraph, blob_store: BlobStore):
    self.kg = kg
    self.blob_store = blob_store

  def import_to_graph(self, rdf_string: bytes) -> str:
    unique_id = str(uuid4())
    url = self.blob_store.upload_file(file_content=rdf_string.encode(), file_name=f"{unique_id}_cobie.ttl", file_type="text/turtle")
    self.kg.import_rdf_data(url)
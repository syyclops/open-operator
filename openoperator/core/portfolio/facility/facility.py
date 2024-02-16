from openoperator.services.knowledge_graph import KnowledgeGraph
from openoperator.services import BlobStore, DocumentLoader, VectorStore, Timescale
from openoperator.core.cobie import COBie
from openoperator.core.bacnet import BACnet 
from openoperator.core.documents import Documents

class Facility:
  """
  This class represents a facility. A facility is a building, a collection of buildings, or a collection of assets.

  It is responsible for:
  - Integration with Documents
  - Integration with the COBie for asset details information
  - Integration with the Building Automation System (BAS)
  """
  def __init__(self, 
    portfolio,
    uri: str,
    knowledge_graph: KnowledgeGraph, 
    blob_store: BlobStore,
    vector_store: VectorStore,
    document_loader: DocumentLoader,
    timescale: Timescale
    ) -> None:
    self.portfolio = portfolio
    self.knowledge_graph = knowledge_graph
    self.uri = uri
    self.blob_store = blob_store
    self.vector_store = vector_store
    self.document_loader = document_loader

    self.documents = Documents(facility=self, knowledge_graph=self.knowledge_graph, blob_store=self.blob_store, document_loader=self.document_loader, vector_store=self.vector_store)
    self.cobie = COBie(self, self.portfolio.operator.embeddings)
    self.bacnet = BACnet(self, self.portfolio.operator.embeddings, timescale)
      
  def details(self) -> dict:
    with self.knowledge_graph.create_session() as session:
      result = session.run("MATCH (n:Facility {uri: $facility_uri}) RETURN n", facility_uri=self.uri)
      return result.data()[0]['n']
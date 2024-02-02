from .knowledge_graph import KnowledgeGraph
from  .blob_store.blob_store import BlobStore
from .vector_store.vector_store import VectorStore
from .document_loader.document_loader import DocumentLoader
from .cobie.cobie import COBie
from uuid import uuid4
import json
from rdflib import Graph, Namespace, Literal, BNode, URIRef
from .utils import create_uri

class Facility:
    """
    This class represents a facility. A facility is a building, a collection of buildings, or a collection of assets.
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
        
    def details(self) -> dict:
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Facility {uri: $facility_uri}) RETURN n", facility_uri=self.uri)
            return result.data()[0]['n']

    def list_files(self) -> list:
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

    
    def search_documents(self, params: dict):
        """
        Search documents in the facility.
        """
        query = params.get("query")
        limit = params.get("limit", 15)
        return self.vector_store.similarity_search(query=query, limit=limit, filter={"facility_uri": self.uri})
    
    def upload_cobie_spreadsheet(self, file: str | bytes) -> (bool, dict | None):
        """
        Convert a cobie spreadsheet to rdf graph, upload it to the blob store and import it to the knowledge graph.
        """
        spreadsheet = COBie(file)
        errors_found, errors, _ = spreadsheet.validate_spreadsheet()
        if errors_found:
            return errors_found, errors
        
        rdf_graph_str = spreadsheet.convert_to_graph(namespace=self.uri)
        id = str(uuid4())
        url = self.blob_store.upload_file(file_content=rdf_graph_str.encode(), file_name=f"{id}_cobie.ttl", file_type="text/turtle")
        self.knowledge_graph.import_rdf_data(url)

        return False, None
    
    def upload_bacnet_data(self, file: bytes):
        """
        This function takes a json file of bacnet data, converts it to rdf and uploads it to the knowledge graph.
        """
        try:
            # Load the file
            data = json.loads(file)

            # Define namespaces for the graph
            RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
            BACNET = Namespace("http://data.ashrae.org/bacnet/#")
            A = RDF['type']

            g = Graph()
            g.bind("bacnet", BACNET)
            g.bind("rdf", RDF)

            # Loop through the bacnet json file
            for item in data:
                if item['Bacnet Data'] == None:
                    continue
                if item['Bacnet Data'] == "{}":
                    continue
                bacnet_data = json.loads(item['Bacnet Data'])[0]

                # Check if the necessary keys are in bacnet_data
                if not all(key in bacnet_data for key in ['device_address', 'device_id', 'device_name']):
                    print("Missing necessary key in bacnet_data, skipping this item.")
                    continue

                device_uri = URIRef(self.uri + '/device/' + bacnet_data['device_address'] + "-" + bacnet_data['device_id'] + '/' + create_uri(bacnet_data['device_name']))
                # Check if its a bacnet device or a bacnet object
                if bacnet_data['object_type'] == "device":
                # Create the bacnet device and add it to the graph
                    g.add((device_uri, A, BACNET.bacnet_Device))

                    # Go through all the bacnet data and add it to the graph
                    for key, value in bacnet_data.items():
                        if key == "object_type":
                            continue
                        g.add((device_uri, BACNET[key], Literal(str(value))))
                else:
                    # Create the bacnet point and add it to the graph
                    point_uri = URIRef(device_uri + '/point/' + bacnet_data['object_type'] + "/" + create_uri(bacnet_data['object_name']) + "/" + bacnet_data['object_index'])
                    g.add((point_uri, A, BACNET.bacnet_Point))

                    # Go through all the bacnet data and add it to the graph
                    for key, value in bacnet_data.items():
                        if key == "object_type":
                            continue
                        g.add((point_uri, BACNET[key], Literal(str(value))))

                    # Create relationship between the device and the point
                    g.add((point_uri, BACNET.objectOf, device_uri))
        
            # Serialize the graph to a file
            graph_string = g.serialize(format='turtle', encoding='utf-8').decode()
            id = str(uuid4())
            url = self.blob_store.upload_file(file_content=graph_string.encode(), file_name=f"{id}_bacnet.ttl", file_type="text/turtle")
            self.knowledge_graph.import_rdf_data(url)
        except Exception as e:
            raise Exception(f"Error uploading bacnet data: {e}")
        
            
        
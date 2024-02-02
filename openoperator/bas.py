import json
from rdflib import Graph, Namespace, Literal, URIRef
from .utils import create_uri
from uuid import uuid4
from .embeddings import Embeddings
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator

class BAS:
    """
    This class handles the integration to the Building Automation System (BAS).

    It is responsible for:

    - Uploading data from BAS to the knowledge graph
    - Converting bacnet data to rdf, and transforming into the brickschema
    - Aligning devices with components from the cobie schema
    """
    def __init__(self, facility, embeddings: Embeddings) -> None:
        self.knowledge_graph = facility.knowledge_graph 
        self.blob_store = facility.blob_store
        self.uri = facility.uri
        self.embeddings = embeddings

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

                if bacnet_data['device_name'] == None or bacnet_data['device_name'] == "":
                    continue

                device_uri = URIRef(self.uri + '/device/' + bacnet_data['device_address'] + "-" + bacnet_data['device_id'] + '/' + create_uri(bacnet_data['device_name']))
                # Check if its a bacnet device or a bacnet object
                if bacnet_data['object_type'] == "device":
                # Create the bacnet device and add it to the graph
                    g.add((device_uri, A, BACNET.Device))

                    # Go through all the bacnet data and add it to the graph
                    for key, value in bacnet_data.items():
                        if key == "object_type":
                            continue
                        g.add((device_uri, BACNET[key], Literal(str(value))))
                else:
                    # Create the bacnet point and add it to the graph
                    point_uri = URIRef(device_uri + '/point/' + bacnet_data['object_type'] + "/" + create_uri(bacnet_data['object_name']) + "/" + bacnet_data['object_index'])
                    g.add((point_uri, A, BACNET.Point))

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
        
    def devices(self):
        """
        Get the bacnet devices in the facility.
        """
        query = "MATCH (d:bacnet__Device) where d.uri starts with $uri RETURN d"
        with self.knowledge_graph.neo4j_driver.session() as session:
            result = session.run(query, uri=self.uri)
            return [record['d'] for record in result.data()]
        
    def points(self, device_uri: str | None = None):
        """
        Get the bacnet points in the facility or a specific device.
        """
        query = "MATCH (p:bacnet__Point)"
        if device_uri:
            query += "-[:bacnet__objectOf]->(d:bacnet__Device {uri: $device_uri})"
        query += " WHERE p.uri STARTS WITH $uri RETURN p"
        with self.knowledge_graph.neo4j_driver.session() as session:
            result = session.run(query, uri=self.uri, device_uri=device_uri)
            return [record['p'] for record in result.data()]
        
    def vectorize_graph(self):
        """
        For each device and point in the facility, create an embedding and upload it to the graph.
        """
        devices = self.devices()

        texts = [device['bacnet__device_name'] for device in devices]

        embeddings = self.embeddings.create_embeddings(texts)

        id_vector_pairs = []
        for i, device in enumerate(devices):
            id_vector_pairs.append({
                "id": device['uri'],
                "vector": np.array(embeddings[i].embedding)
            })

        # Upload the vectors to the graph
        query = """UNWIND $id_vector_pairs as pair
                    MATCH (n:bacnet__Device) WHERE n.uri = pair.id
                    CALL db.create.setNodeVectorProperty(n, 'embedding', pair.vector)
                    RETURN n"""
        try:
            with self.knowledge_graph.neo4j_driver.session() as session:
                session.run(query, id_vector_pairs=id_vector_pairs)
        except Exception as e:
            raise Exception(f"Error uploading vectors to the graph: {e}")
        
        points = self.points()
        texts = [point['bacnet__object_name'] for point in points]

        embeddings = self.embeddings.create_embeddings(texts)

        id_vector_pairs = []
        for i, point in enumerate(points):
            id_vector_pairs.append({
                "id": point['uri'],
                "vector": np.array(embeddings[i].embedding)
            })

        # Upload the vectors to the graph
        query = """UNWIND $id_vector_pairs as pair
                    MATCH (n:bacnet__Point) WHERE n.uri = pair.id
                    CALL db.create.setNodeVectorProperty(n, 'embedding', pair.vector)
                    RETURN n"""
        
        try:
            with self.knowledge_graph.neo4j_driver.session() as session:
                session.run(query, id_vector_pairs=id_vector_pairs)
        except Exception as e:
            raise Exception(f"Error uploading vectors to the graph: {e}")
        

    def dbscan_cluster(self, X):
        print("Clustering...")
        # Find the optimal epsilon
        nbrs = NearestNeighbors(n_neighbors=5).fit(X)

        distances, indices = nbrs.kneighbors(X)

        distances = np.sort(distances, axis=0)

        kneedle = KneeLocator(
            range(1, distances.shape[0] + 1), distances[:, 1], curve="convex", direction="increasing"
        )

        db = DBSCAN(eps=kneedle.knee_y, min_samples=3).fit(X)
        labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)

        print(f"Estimated number of clusters: {n_clusters_}")
        print(f"Estimated number of noise points: {n_noise_}")

        return labels
        
    def cluster_devices(self):
        devices = self.devices()

        embeddings = [device['embedding'] for device in devices]
        embeddings = np.vstack(embeddings)

        cluster_assignments = self.dbscan_cluster(embeddings)

        # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
        clusters = {}
        for i in range(len(cluster_assignments)):
            cluster = cluster_assignments[i]
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(devices[i]['bacnet__device_name']) 

        return clusters
    
    def cluster_points(self):
        points = self.points()

        embeddings = [point['embedding'] for point in points]
        embeddings = np.vstack(embeddings)

        cluster_assignments = self.dbscan_cluster(embeddings)

        # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
        clusters = {}
        for i in range(len(cluster_assignments)):
            cluster = cluster_assignments[i]
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(points[i]['bacnet__object_name'])
        
        return clusters




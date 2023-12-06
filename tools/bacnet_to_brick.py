from rdflib import Namespace
from brickschema import Graph
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
from langchain.vectorstores import Chroma
import chromadb
from langchain.schema import Document
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
import argparse
import numpy as np
from langchain.embeddings.openai import OpenAIEmbeddings
load_dotenv()

# Create the OpenAI client
client = OpenAI()

# Create the Chroma client
chroma_client = chromadb.Client()
langchain_chroma = Chroma(
    client=chroma_client,
    collection_name="test",
    embedding_function=OpenAIEmbeddings(),
)

# Define namespaces for the graph
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SYYCLOPS = Namespace('https://syyclops.com/')
BRICK = Namespace("https://brickschema.org/schema/Brick#")
BACNET = Namespace("http://data.ashrae.org/bacnet/2016#")
A = RDF['type']


"""
This function finds the optimal number of clusters for KMeans clustering.
It uses the silhouette score to determine the optimal number of clusters.

Parameters:
    X (np.array): The data to be clustered.
    kmin (int, optional): The minimum number of clusters to test. Defaults to 2.
    kmax (int, optional): The maximum number of clusters to test. Defaults to 200.
    batch_size (int, optional): The batch size to use for MiniBatchKMeans. Defaults to 1000.
    patience (int, optional): The number of iterations to wait for the silhouette score to improve before stopping. Defaults to 5.
    step_size (int, optional): The step size to use when iterating through the number of clusters. Defaults to 10.

Returns:
    int: The optimal number of clusters.
"""
def find_optimal_k(X, kmin=2, kmax=200, batch_size=1000, patience=5, step_size=10):
    print("Finding optimal number of clusters...")
    sil = [] # list of silhouette scores
    counter = 0
    best_score = -1
    k_values = []

    for k in tqdm(range(kmin, kmax+1, step_size)):
        kmeans = MiniBatchKMeans(n_clusters=k, n_init=10, random_state=0, batch_size=batch_size).fit(X) # adjust batch_size as needed
        labels = kmeans.labels_
        score = silhouette_score(X, labels, metric='euclidean')
        sil.append(score)
        k_values.append(k)

        # Early stopping with patience
        if score > best_score:
            best_score = score
            counter = 0  # reset counter when score improves
        else:
            counter += 1  # increment counter when score does not improve
            if counter >= patience:
                break

    optimal_clusters = k_values[np.argmax(sil)]  # get the optimal number of clusters

    return optimal_clusters

"""
This function performs KMeans clustering on the given data.

Parameters:
    X (np.array): The data to be clustered.
    k (int): The number of clusters.

Returns:
    tuple: A tuple containing the cluster assignments and the labels.
"""
def kmeans_clustering(X: np.array, k: int):
    print("Clustering...")
    kmeans = KMeans(n_clusters=k, random_state=0, n_init=10)
    cluster_assignments = kmeans.fit_predict(X)
    labels = kmeans.labels_

    return cluster_assignments, labels


"""
This function vectorizes the bacnet graph. It creates documents for each device and point in the graph,
and loads these documents into the vector store. It uses SPARQL queries to extract the necessary information
from the graph.

Parameters:
    g (Graph): The bacnet graph to be vectorized.

Returns:
    tuple: A tuple containing the device documents and the point documents.
"""
def vectorize_bacnet_graph(g):
    print("Vectorizing bacnet graph...")
    # Create the documents to load into the vector store
    device_documents = []

    # Define a SPARQL query for bacnet_Device
    query_for_devices = """
        PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

        SELECT ?device ?device_name
            WHERE {
            ?device a bacnet:bacnet_Device ;
                    bacnet:device_name ?device_name .
            }
        """
    try:
        # Run the query for devices
        for row in g.query(query_for_devices):
            device_uri = row[0]
            device_name = row[1]

            # Create the document
            content = device_name.value
            device_documents.append(Document(page_content=content, metadata={"type": "bacnet_device", "uri": device_uri}))

        # Load the documents into the vector store
        langchain_chroma.add_documents(device_documents)
        
        points_documents = []

        # Define query for bacnet_Point
        query_for_points = """
            PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

            SELECT ?point ?device_name ?point_name ?present_value ?unit
            WHERE {
            ?point a bacnet:bacnet_Point ;
                    bacnet:device_name ?device_name ;
                    bacnet:object_name ?point_name ;
                    bacnet:present_value ?present_value ;
                    bacnet:object_units ?unit .
            }
            """
        
        # Run the query for points
        for row in g.query(query_for_points):
            point, device_name, point_name, present_value, unit = row
            
            content = point_name.value + " " + present_value.value + " " + unit.value
            points_documents.append(Document(page_content=content, metadata={"type": "bacnet_point", "uri": point}))

        # Load the documents into the vector store
        langchain_chroma.add_documents(points_documents)

        return device_documents, points_documents
    except Exception as e:
        print(f"Error while vectorizing bacnet graph: {e}")


def load_brick_equipment_types():
    print("Loading brick schema equipment types into vector store...")
    # Load all the brick classes for equipment from brick_equipment_list.txt into the vector store
    with open("../brick_equipment_list.txt", "r") as f:
        brick_equipment_list = f.read()

    # Create the documents to load into the vector store
    documents = []

    # Loop through the brick equipment list
    for line in tqdm(brick_equipment_list.split("\n")):
        content = line

        # Create a document
        document = Document(page_content=content, metadata={"type": "brick_equipment"})
        documents.append(document)

    langchain_chroma.add_documents(documents)

    return documents

def load_brick_point_types():
    print("Loading brick schema point types into vector store...")
    # Load all the brick classes for points from brick_point_list.txt
    with open("../brick_point_list.txt", "r") as f:
        brick_point_list = f.read()

    # Create an array of all the brick classes for points by separating by commas
    brick_point_list = brick_point_list.split(",")

    # Create the documents to load into the vector store
    documents = []

    # Loop through the brick point list
    for line in tqdm(brick_point_list):
        content = line

        # Create a document
        document = Document(page_content=content, metadata={"type": "brick_point"})
        documents.append(document)

    langchain_chroma.add_documents(documents)

    return documents


def classify_bacnet_clusters(clusters: dict, g: Graph, filter_type: str):
    try:
        print(f"Classifying {type} clusters...")
        for cluster in tqdm(clusters):
            cluster = clusters[cluster] # Get the cluster from the dictionary
            
            device_names = []
            for document in cluster:
                device_names.append(document.page_content)

            # Similarity search for the device name
            results = langchain_chroma.similarity_search("\n".join(device_names), k=10, filter={"type": filter_type})

            # Get the page content for the similar brick classes
            similar_brick_classes = [result.page_content for result in results]

            # Create the prompt
            device_classifier_prompt = """You are bacnet to brick schema classifier. You are given a cluster of bacnet device names or object data and you output the correct brick schema classification class. You are given the options of brick classes to choose from, select the one that makes the most sense for the bacnet cluster.

You ONLY output the brick class. 
You ONLY output one brick class. 
You ONLY select a brick class from the provided brick schema class options. 
If the brick class is unknown output N/A."""
            
            input = "BRICK SCHEMA CLASS OPTIONS:\n"
            input += "\n".join(similar_brick_classes) + "\n\n"
            input += "BACNET Cluster:\n"
            input += "\n".join(device_names)

            print(device_classifier_prompt)
            print()
            print(input)
            print()

            messages = [
                {
                    "role": "system",
                    "content": device_classifier_prompt
                },
                {
                    "role": "user",
                    "content": input
                }
            ]

            # Send the prompt to the API
            res = client.chat.completions.create(messages=messages, model="gpt-3.5-turbo-1106", temperature=0, max_tokens=100)

            # Get the response
            response = res.choices[0].message.content

            print(response)
            print()
            print()

            # Remove any whitespace at the beginning or end
            response = response.strip()

            if response != "N/A":
                # Replace all whitespace with _
                brick_class = BRICK[response.replace(" ", "_")]

                # Add the brick class to the graph
                for document in cluster:
                    g.add((document.metadata["uri"], A, brick_class))

            # wait some time so we don't get rate limited
            # time.sleep(25)
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    # Create arguments
    parser = argparse.ArgumentParser(description='Generate Brick Graph from BACnet JSON file')
    parser.add_argument('--path', type=str, help='path to the BACnet ttl file')
    parser.add_argument('--customerName', type=str, help='name of the customer')
    parser.add_argument('--buildingName', type=str, help='name of the building')
    parser.add_argument('--output', type=str, help='path to the output file')
    parser.parse_args()
    path = parser.parse_args().path
    customer_name = parser.parse_args().customerName
    building_name = parser.parse_args().buildingName
    output = parser.parse_args().output

    assert path, 'Path to BACnet JSON file must be specified'
    assert customer_name, 'Customer name must be specified'
    assert building_name, 'Building name must be specified'
    assert output, 'Output file must be specified'

    # Load the graph
    print("Loading graph...")
    g = Graph(load_brick=True)
    g.bind('brick', BRICK)
    g.bind('rdf', RDF)
    g.load_file(path, format="turtle")

    # Load the brick equipment types into the vector store
    load_brick_equipment_types()
    load_brick_point_types()

    # Vectorize the bacnet graph data
    device_documents, points_documents = vectorize_bacnet_graph(g)

    # Get the embeddings of the bacnet devices
    device_embds = langchain_chroma.get(include=["embeddings", "metadatas"], where={"type": "bacnet_device"})
    device_embds = device_embds["embeddings"]
    device_embds = np.vstack(device_embds)

    # Find the optimal number of clusters for the bacnet devices
    optimal_clusters = find_optimal_k(device_embds, kmin=2, kmax=40, step_size=1)
    print("Optimal number of clusters of bacnet devices: " + str(optimal_clusters))

    # Cluster the bacnet devices
    cluster_assignments, labels = kmeans_clustering(device_embds, optimal_clusters)

    # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
    clusters = {}
    for i in range(len(cluster_assignments)):
        cluster = cluster_assignments[i]
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(device_documents[i]) 

    # Classify the bacnet devices
    classify_bacnet_clusters(clusters, g, filter_type="brick_equipment")

    # Get the embeddings of the bacnet points
    points_embds = langchain_chroma.get(include=["embeddings", "metadatas"], where={"type": "bacnet_point"})
    points_embds = points_embds["embeddings"]
    points_embds = np.vstack(points_embds)

    # Find the optimal number of clusters for the bacnet points
    optimal_clusters = find_optimal_k(points_embds, kmin=260, kmax=360, step_size=5)
    print("Optimal number of clusters of bacnet points: " + str(optimal_clusters))

    # Cluster the bacnet points
    cluster_assignments, labels = kmeans_clustering(points_embds, optimal_clusters)

    # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
    clusters = {}
    for i in range(len(cluster_assignments)):
        cluster = cluster_assignments[i]
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(points_documents[i])

    # Classify the bacnet points
    classify_bacnet_clusters(clusters, g, filter_type="brick_point")
    
    # Save the graph
    print(f"Before: {len(g)} triples")
    g.expand("rdfs")
    print(f"After: {len(g)} triples")
    g.serialize(output, format="turtle")
    
if __name__ == "__main__":
    main()
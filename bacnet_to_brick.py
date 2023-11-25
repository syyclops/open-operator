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


def find_optimal_k(X, kmin=2, kmax=200, sample_size=10000, batch_size=1000):
    print("Finding optimal number of clusters...")
    sil = [] # list of silhouette scores

    for k in tqdm(range(kmin, kmax+1)):
        kmeans = MiniBatchKMeans(n_clusters=k, n_init=10).fit(X) # adjust batch_size as needed
        labels = kmeans.labels_
        sil.append(silhouette_score(X, labels, metric='euclidean')) # adjust sample_size as needed

        # Early stopping
        if k > 2 and sil[k-kmin] < sil[k-kmin-1]:
            break

    optimal_clusters = np.argmax(sil) + kmin  # +kmin because the range starts from kmin

    return optimal_clusters

def kmeans_clustering(X, k):
    print("Clustering...")
    kmeans = KMeans(n_clusters=k, random_state=0)
    cluster_assignments = kmeans.fit_predict(X)
    labels = kmeans.labels_

    return cluster_assignments, labels


def load_bacnet_devices(g):
    print("Loading bacnet devices into vector store...")
    # Create the documents to load into the vector store
    documents = []

    # Define a SPARQL query for bacnet_Device
    query_for_devices = """
    PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

    SELECT ?device ?device_name
        WHERE {
        ?device a bacnet:bacnet_Device ;
                bacnet:device_name ?device_name .
        }
    """

    # Run the query for devices
    for row in g.query(query_for_devices):
        device_uri = row[0]
        device_name = row[1]

        # Create the document
        content = device_name.value
        documents.append(Document(page_content=content, metadata={"type": "bacnet_device", "uri": device_uri}))
    
    langchain_chroma.add_documents(documents)

    return documents


def load_brick_equipment_types():
    print("Loading brick schema equipment types into vector store...")
    # Load all the brick classes for equipment from brick_equipment_list.txt into the vector store
    with open("./brick_equipment_list.txt", "r") as f:
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
    with open("./brick_point_list.txt", "r") as f:
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


def classify_bacnet_device_cluster(cluster, g):
    print("Classifying a cluster of devices...")
    device_names = []
    for document in cluster:
        device_names.append(document.page_content)

    # Similarity search for the device name
    results = langchain_chroma.similarity_search("\n".join(device_names), k=10, filter={"type": "brick_equipment"})

    # Get the page content for the similar brick classes
    similar_brick_classes = [result.page_content for result in results]

    # Create the prompt
    device_classifier_prompt = """You are a system that is given a cluster bacnet device names and you output whats its correct brick schema classification class is for the cluster. ONLY output the brick class. ONLY output one brick class. ONLY select a brick class from the provided brick equipment types. If the brick class is unknown output N/A.\n\n"""
    device_classifier_prompt += """BRICK SCHEMA EQUIPMENT TYPES:\n\n"""
    device_classifier_prompt += "\n".join(similar_brick_classes) + "\n"

    messages = [
        {
            "role": "system",
            "content": device_classifier_prompt
        },
        # {
        #     "role": "user",
        #     "content": "AHU-1\nAHU-2\nAHU-5"
        # },
        # {
        #     "role": "assistant",
        #     "content": "AHU"
        # },
        {
            "role": "user",
            "content": "\n".join(device_names)
        }
    ]

    # Send the prompt to the API
    res = client.chat.completions.create(messages=messages, model="gpt-4-1106-preview")

    # Get the response
    response = res.choices[0].message.content

    # Remove any whitespace at the beginning or end
    response = response.strip()

    if response != "N/A":
        # Replace all whitespace with _
        brick_class = BRICK[response.replace(" ", "_")]

        # Add the brick class to the graph
        for document in cluster:
            g.add((document.metadata["uri"], A, brick_class))


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
    g = Graph()
    g.bind('brick', BRICK)
    g.bind('rdf', RDF)
    g.load_file(path, format="turtle")

    # Load the brick equipment types into the vector store
    load_brick_equipment_types()
    load_brick_point_types()
    # Load the bacnet devices into the vector store
    documents = load_bacnet_devices(g)

    # Get the embeddings of the bacnet devices
    device_embds = langchain_chroma.get(include=["embeddings", "metadatas"], where={"type": "bacnet_device"})
    device_embds = device_embds["embeddings"]
    device_embds = np.vstack(device_embds)

    # Find the optimal number of clusters
    optimal_clusters = find_optimal_k(device_embds)

    # Cluster the bacnet devices
    cluster_assignments, labels = kmeans_clustering(device_embds, optimal_clusters)

    # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
    clusters = {}
    for i in range(len(cluster_assignments)):
        cluster = cluster_assignments[i]
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(documents[i]) 

    # Classify each cluster
    for cluster in clusters:
        classify_bacnet_device_cluster(clusters[cluster], g=g)

    
    # Save the graph
    print(f"Before: {len(g)} triples")
    g.expand("rdfs")
    print(f"After: {len(g)} triples")
    g.serialize(output, format="turtle")
        
    
    # Print the clusters
    # for cluster in clusters:
    #     print("Cluster " + str(cluster) + ":")
    #     for document in clusters[cluster]:
    #         print(document.metadata["uri"])
    #     print()
    

if __name__ == "__main__":
    main()


# # # Define a SPARQL query for bacnet_Device
# # query_for_devices = """
# # PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

# # SELECT ?device ?device_name
# # WHERE {
# #   ?device a bacnet:bacnet_Device ;
# #           bacnet:device_name ?device_name .
# # }
# # """

# # print("Classifying devices...")
# # # Run the query for devices
# # for row in tqdm(g.query(query_for_devices)):
# #     device_uri = row[0]
# #     device_name = row[1]

# #     # Similarity search for the device name
# #     results = db.similarity_search(device_name.value, k=10)

# #     # Get the page content for the similar brick classes
# #     similar_brick_classes = [result.page_content for result in results]

# #     # Create the prompt
# #     device_classifier_prompt = """BRICK SCHEMA EQUIPMENT TYPES:\n\n"""
# #     device_classifier_prompt += "\n".join(similar_brick_classes) + "\n"
# #     device_classifier_prompt += """\nYou are a system that is given a bacnet device name and you output whats its correct brick schema classification class is. ONLY output the brick class. If the brick class is unknown output N/A.
    
# # Device name: AHU-1

# # Brick Class: AHU

# # Device name:"""

# #     input = device_classifier_prompt + device_name + "\n" + "Brick Class: "

# #     # Send the prompt to the API
# #     response = client.completions.create(
# #       model="gpt-3.5-turbo-instruct",
# #       prompt=input,
# #       temperature=0
# #     )

# #     # Get the response
# #     response = response.choices[0].text

# #     # Remove any whitespace at the beginning or end
# #     response = response.strip()

# #     if response != "N/A":
# #         # Replace all whitespace with _
# #         brick_class = BRICK[response.replace(" ", "_")]

# #         # Add the brick class to the graph
# #         g.add((device_uri, A, brick_class))


# # # Load all the brick classes for points from brick_point_list.txt
# with open("./brick_point_list.txt", "r") as f:
#     brick_point_list = f.read()

# # Create an array of all the brick classes for points by separating by commas
# brick_point_list = brick_point_list.split(",")

# print("Loading brick schema point types into vector store...")
# # Load all the brick classes for points from brick_point_list.txt into the vector store
# for line in tqdm(brick_point_list):
#     content = line

#     # Create a document
#     document = Document(page_content=content, metadata={"type": "brick_point"})
#     documents.append(document)

# # Load the documents into the vector store
# db = Chroma.from_documents(documents, OpenAIEmbeddings()) 


# # Define a SPARQL query for bacnet_Point
# query_for_points = """
# PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

# SELECT ?point ?device_name ?point_name ?present_value ?unit ?object_type ?description
# WHERE {
#   ?point a bacnet:bacnet_Point ;
#          bacnet:device_name ?device_name ;
#          bacnet:object_name ?point_name ;
#          bacnet:present_value ?present_value ;
#          bacnet:object_units ?unit ;
#          bacnet:raw_object_type ?object_type ;
#          bacnet:object_description ?description .
# }
# """

# print("Classifying points...")
# try :
#     # Run the query for points
#     for row in tqdm(g.query(query_for_points)):
#         point, device_name, point_name, present_value, unit, object_type, description = row
        
#         input = "Bacnet Device Name: " + device_name.value + "\n" + "Bacnet Point Name: " + point_name.value + "\n" + "Bacnet Point Present Value: " + present_value.value + "\n" + "Bacnet Point Unit: " + unit.value + "\n" + "Bacnet Point Description: " + description.value + "\n"

#         # Similarity search for the point name
#         results = db.similarity_search(point_name.value, k=10)

#         # Get the page content for the similar brick classes
#         similar_brick_classes = [result.page_content for result in results]

#         point_classifier_sys_message = """BRICK SCHEMA POINTS:\n\n"""
#         point_classifier_sys_message += "\n".join(similar_brick_classes) + "\n"
#         point_classifier_sys_message += """\nYou are a system that is given bacnet object information and you output whats its correct brick schema classification class is. ONLY output the brick class. If the brick class is unknown output N/A."""


#         messages = [
#             {
#                 "role": "system",
#                 "content": point_classifier_sys_message
#             },
#             {
#                 "role": "user",
#                 "content": input
#             }
#         ]

#         # Send the prompt to the API
#         res = client.chat.completions.create(messages=messages, model="gpt-3.5-turbo")

#         # Get the response
#         response = res.choices[0].message.content

#         # Remove any whitespace at the beginning or end
#         response = response.strip()

#         if response != "N/A":
#             # Replace all whitespace with _
#             brick_class = BRICK[response.replace(" ", "_")]

#             # Add the brick class to the graph
#             g.add((point, A, brick_class))  
# except KeyboardInterrupt:
#     print("Keyboard Interrupt, saving graph...")
#     # Run inference on the graph to add inferred types
#     g.expand("rdfs")
#     g.serialize("data/dunbar/brick.ttl", format="turtle")
    
# # Run inference on the graph to add inferred types
# g.expand("rdfs")
# # Save the graph
# g.serialize("data/dunbar/brick.ttl", format="turtle")
from rdflib import Graph, Namespace
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import tiktoken
load_dotenv()

client = OpenAI()


### Give all the bacnet device a brick class

device_classifier_prompt = """BRICK SCHEMA EQUIPMENT TYPES:\n\n"""

# Read in all brick schema equipment types from brick_equipment_list.txt.
# This is used to create the prompt for the GPT-3 API.
with open("./brick_equipment_list.txt", "r") as f:
    brick_equipment_list = f.read()
    
# Add the brick equipment list to the prompt
device_classifier_prompt = device_classifier_prompt + brick_equipment_list

device_classifier_prompt += """\nYou are a system that is given a bacnet device name and you output whats its correct brick schema classification class is. ONLY output the brick class. If the brick class is unknown output N/A.
    
Device name: AHU-1

Brick Class: AHU

Device name:"""

# Define Namespace
BRICK = Namespace("https://brickschema.org/schema/Brick#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
A = RDF['type']

# Load the graph
g = Graph()
g.bind('brick', BRICK)
g.bind('rdf', RDF)
g.parse("data/dunbar/bacnet.ttl", format="turtle")


# Define a SPARQL query for bacnet_Device
query_for_devices = """
PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

SELECT ?device ?device_name
WHERE {
  ?device a bacnet:bacnet_Device ;
          bacnet:device_name ?device_name .
}
"""

print("Classifying devices...")
# Run the query for devices
# for row in tqdm(g.query(query_for_devices)):
#     device_uri = row[0]
#     device_name = row[1]

#     input = device_classifier_prompt + device_name + "\n" + "Brick Class: "

#     response = client.completions.create(
#       model="gpt-3.5-turbo-instruct",
#       prompt=input,
#       temperature=0
#     )

#     # Get the response
#     response = response.choices[0].text

#     # Remove any whitespace at the beginning or end
#     response = response.strip()

#     if response != "N/A":
#         # Replace all whitespace with _
#         brick_class = BRICK[response.replace(" ", "_")]

#         # Add the brick class to the graph
#         g.add((device_uri, A, brick_class))


### Give all the bacnet points a brick class

# Load all the brick classes for points from brick_point_list.txt
with open("./brick_point_list.txt", "r") as f:
    brick_point_list = f.read()

point_classifier_sys_message = """BRICK SCHEMA POINTS:\n\n"""
point_classifier_sys_message += brick_point_list + "\n"
point_classifier_sys_message += """You are a system that is given bacnet object information and you output whats its correct brick schema classification class is. ONLY output the brick class. If the brick class is unknown output N/A."""

# Define a SPARQL query for bacnet_Point
query_for_points = """
PREFIX bacnet: <http://data.ashrae.org/bacnet/2016#>

SELECT ?point ?device_name ?point_name ?present_value ?unit ?object_type ?description
WHERE {
  ?point a bacnet:bacnet_Point ;
         bacnet:device_name ?device_name ;
         bacnet:object_name ?point_name ;
         bacnet:present_value ?present_value ;
         bacnet:object_units ?unit ;
         bacnet:raw_object_type ?object_type ;
         bacnet:object_description ?description .
}
"""

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
  """Returns the number of tokens used by a list of messages."""
  try:
      encoding = tiktoken.encoding_for_model(model)
  except KeyError:
      encoding = tiktoken.get_encoding("cl100k_base")
  if model == "gpt-3.5-turbo-0613":  # note: future models may deviate from this
      num_tokens = 0
      for message in messages:
          num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
          for key, value in message.items():
              num_tokens += len(encoding.encode(value))
              if key == "name":  # if there's a name, the role is omitted
                  num_tokens += -1  # role is always required and always 1 token
      num_tokens += 2  # every reply is primed with <im_start>assistant
      return num_tokens
  else:
      raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")

print("Classifying points...")
# Run the query for points
for row in tqdm(g.query(query_for_points)):
    point, device_name, point_name, present_value, unit, object_type, description = row
    
    input = "Bacnet Device Name: " + device_name.value + "\n" + "Bacnet Point Name: " + point_name.value + "\n" + "Bacnet Point Present Value: " + present_value.value + "\n" + "Bacnet Point Unit: " + unit.value + "\n" + "Bacnet Point Description: " + description.value + "\n"

    messages = [
        {
            "role": "system",
            "content": point_classifier_sys_message
        },
        {
            "role": "user",
            "content": input
        }
    ]

    num_tokens = num_tokens_from_messages(messages)
    print("Number of tokens:", num_tokens)

    # res = client.chat.completions.create(messages=messages, model="gpt-4-1106-preview")

    # response = res.choices[0].message.content
    

    # # Remove any whitespace at the beginning or end
    # response = response.strip()

    # if response != "N/A":
    #     # Replace all whitespace with _
    #     brick_class = BRICK[response.replace(" ", "_")]

    #     # Add the brick class to the graph
    #     g.add((point, A, brick_class))

# Run inference on the graph to add inferred types
g.expand("rdfs")
# Save the graph
g.serialize("data/dunbar/brick.ttl", format="turtle")

# If the user exits the program, save the graph
import atexit
atexit.register(g.serialize, "data/dunbar/brick.ttl", format="turtle")
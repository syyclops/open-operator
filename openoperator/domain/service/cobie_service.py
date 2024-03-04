from openoperator.domain.repository import COBieRepository
from openoperator.domain.model import COBieSpreadsheet
from openoperator.utils import create_uri
from typing import Tuple, Dict
import pandas as pd
import rdflib
from rdflib import Namespace, Literal, RDF
from io import BytesIO

class COBieService:
  def __init__(self, cobie_repository: COBieRepository):
    self.cobie_repository = cobie_repository

  def process_cobie_spreadsheet(self, facility_uri, file: str | bytes, validate: bool = True) -> Tuple[bool, Dict]:
    spreadsheet = COBieSpreadsheet(file)
    if validate:
      errors_found, errors, _ = spreadsheet.validate()
      if errors_found:
        return errors_found, errors
    
    rdf_graph_str = self.convert_to_rdf(facility_uri, file)
    self.cobie_repository.import_to_graph(rdf_graph_str)

    return False, None
  
  def convert_to_rdf(self, facility_uri: str, file_content: bytes) -> str:
    """
    Converts a valid COBie spreadsheet to RDF and uploads it to knowledge graph.
    """
    namespace = Namespace(facility_uri)

    # Open COBie spreadsheet
    df = pd.read_excel(BytesIO(file_content), engine='openpyxl', sheet_name=None)

    # Define common namespaces
    COBIE = Namespace("http://checksem.u-bourgogne.fr/ontology/cobie24#")
    A = RDF.type

    # Create an rdflib Graph to store the RDF data
    g = rdflib.Graph()
    g.bind("RDF", RDF)
    g.bind("COBIE", COBIE)
    g.bind("Namespace", namespace)
    facility_uri = namespace # All the nodes in the graph will extend this uri

    for sheet in ['Floor', 'Space', 'Type', 'Component', 'System']:
      print(f"Processing {sheet} sheet...")
      predicates = df[sheet].keys()
      predicates = [predicate[0].lower() + predicate[1:] for predicate in predicates] # Make first letter lowercase

      # Iterate over all rows in the sheet, skipping the first row
      for _, row in df[sheet].iterrows():
        # The name field is used as the subject
        subject = row['Name']
        subject_uri = facility_uri["/" + sheet.lower() + "/" + create_uri(subject)]

        # Get the values of the row
        objects = row.values

        # Create the node
        g.add((subject_uri, A, COBIE[sheet]))

        # Add objects
        i = 0
        for obj in objects:
          if pd.isnull(obj): # Make sure the object is not None
            continue
          predicate = predicates[i]

          # Check if it should be a relationship or a literal
          if (sheet == "Component" and predicate == "typeName") or (sheet == "Space" and predicate == "floorName") or (sheet == "System" and predicate == "componentNames"):
            # The target sheet is the one where the relationship is pointing to 
            target_sheet = None
            if sheet == "Component":
              target_sheet = "Type"
            elif sheet == "Space":
              target_sheet = "Floor"
            elif sheet == "System":
              target_sheet = "Component"
        
            g.add((subject_uri, COBIE[predicate], facility_uri["/" + target_sheet.lower() + "/" + create_uri(obj)]))
          elif sheet == "Component" and predicate == "space":
            # Split by "," to get all spaces and remove whitespace
            spaces = [space.strip() for space in str(obj).split(",")]
            for space in spaces:
              g.add((subject_uri, COBIE[predicate], facility_uri["/" + "space" + "/" + create_uri(space)]))
          else:
            g.add((subject_uri, COBIE[predicate], Literal(str(obj).replace('"', '\\"'))))
          i += 1      

    # Create the attributes
    print("Processing Attribute sheet...")
    # for _, row in df['Attribute'].iterrows():
    #   target_sheet = row['SheetName']
    #   target_row_name = row['RowName']
    #   target_uri = facility_uri["/" + target_sheet.lower() + "/" + create_uri(target_row_name)]

    #   attribute_uri = target_uri + "/attribute/" + create_uri(row['Name'])

    #   g.add((attribute_uri, A, COBIE['Attribute']))
    #   g.add((attribute_uri, COBIE['name'], Literal(row['Name'])))
    #   g.add((attribute_uri, COBIE['value'], Literal(row['Value'])))
    #   g.add((attribute_uri, COBIE['unit'], Literal(row['Unit'])))
    #   g.add((attribute_uri, COBIE['attributeTo'], target_uri))

    # Serialize the graph to a file
    graph_string = g.serialize(format='turtle', encoding='utf-8').decode()

    return graph_string
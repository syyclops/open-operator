
import pandas as pd
import rdflib
from rdflib import Namespace, Literal
import urllib.parse
from ...services.blob_store import BlobStore
from ...services.graph_db import GraphDB

# Define common namespaces
COBIE = Namespace("http://checksem.u-bourgogne.fr/ontology/cobie24#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
A = RDF.type

class COBie:
    """
    This class handles everything related to the COBie graph.

    Its repsonsibilities are to:

    1. COBie spreadsheet validation
    2. Spreadsheet to RDF conversion
    """
    def __init__(self, graph_db: GraphDB, blob_store: BlobStore) -> None:
        self.graph_db = graph_db
        self.blob_store = blob_store

    def create_uri(self, name: str) -> str:
        """
        Create a URI from string.
        """
        # name = re.sub(r'[^a-zA-Z0-9]', '', str(name).lower())
        # name = name.replace("'", "_")  # Replace ' with _
        name = urllib.parse.quote(name.lower())
        return name

    def validate_spreadsheet(self, df) -> list:
        """
        Validate a COBie spreadsheet. Refer to COBie_validation.pdf in docs/ for more information.
        Returns a list of errors. If no errors are found, the list will be empty.
        """
        errors = []

        expected_sheets = ['Facility', 'Floor', 'Space', 'Type', 'Component', 'Attribute', 'System']
        # Check to make sure the spreadsheet has the correct sheets     
        for sheet in expected_sheets:
            if sheet not in df.keys():
                errors.append(f"Expected sheet {sheet} not found in spreadsheet.")

        # Make sure there is only one record in the Facility sheet
        if len(df['Facility']) > 1:
            errors.append("More than one record found in Facility sheet.")

        # No empty or N/A cells are present in column A of any sheet
        for sheet in expected_sheets:
            if df[sheet]['Name'].isnull().values.any():
                errors.append(f"Empty or N/A cells found in column A of {sheet} sheet.")

        # Check Floor, Space, Type, Component sheets for duplicate names in column A
        for sheet in ['Floor', 'Space', 'Type', 'Component']:
            if df[sheet]['Name'].duplicated().any():
                errors.append(f"Duplicate names found in column A of {sheet} sheet.")

        # Space Tab
        # Every value is linked to a value in the first column of the Floor tab
        for space in df['Space']['FloorName'].unique():
            if space not in df['Floor']['Name'].values:
                errors.append(f"Space {space} is not linked to a value in the first column of the Floor tab.")

        # Type Tab
        # Every record has a category
        if df['Type']['Category'].isnull().values.any():
            errors.append("Not every record has a category.")

        # Component Tab
        # Every record is linked to a existing Type
        for component in df['Component']['TypeName'].unique():
            if component not in df['Type']['Name'].values:
                errors.append(f"Component {component} is not linked to an existing Type.")
        # Every record is linked a to existing Space
        for space_name in df['Component']['Space'].unique():
            # Check if cell is valid
            if pd.isnull(space_name):
                errors.append("Not every record is linked to an existing Space.")
                continue
            # Split by "," to get all spaces and remove whitespace
            spaces = [space.strip() for space in space_name.split(",")]
            for space in spaces:
                if space not in df['Space']['Name'].values:
                    errors.append(f"Space {space_name} is not linked to an existing Space.")
        
        return errors

    def upload_spreadsheet(self, file_path: str, portfolio_namespace: str) -> list | None:
        """
        Converts a valid COBie spreadsheet to RDF and uploads it to knowledge graph.

        Portfolio namespace is the namespace to represent a group of buildings. For example, https://departmentOfEnergy.com/ could be the namespace for all the buildings owned by the Department of Energy.
        The portfolio namespace is used to create a URI for the facility. For example, if the portfolio namespace is https://departmentOfEnergy.com/ and the facility name is "Building 1", then the facility URI will be https://departmentOfEnergy.com/building_1.
        The facility name comes from the Facility sheet in the COBie spreadsheet.
        """
        # Make sure the portfolio namespace is a valid URI
        assert urllib.parse.urlparse(portfolio_namespace).scheme != ""
        portfolio_namespace = Namespace(portfolio_namespace)

        # Open COBie spreadsheet
        df = pd.read_excel(file_path, engine='openpyxl', sheet_name=None)

        errors = self.validate_spreadsheet(df)

        if errors:
            print("Errors found in the spreadsheet:")
            return errors
        else:
            print("No errors found in the spreadsheet.")

            # Create an rdflib Graph to store the RDF data
            g = rdflib.Graph()
            g.bind("RDF", RDF)
            g.bind("COBIE", COBIE)
            g.bind("Namespace", portfolio_namespace)

            facility_uri = portfolio_namespace[self.create_uri(df['Facility']['Name'][0])] # All the nodes in the graph will extend this uri

            for sheet in ['Facility', 'Floor', 'Space', 'Type', 'Component', 'System']:
                print(f"Processing {sheet} sheet...")
                predicates = df[sheet].keys()
                predicates = [predicate[0].lower() + predicate[1:] for predicate in predicates] # Make first letter lowercase

                # Iterate over all rows in the sheet, skipping the first row
                for _, row in df[sheet].iterrows():
                    # The name field is used as the subject
                    subject = row['Name']
                    subject_uri = facility_uri + "/" + sheet.lower() + "/" + self.create_uri(subject)

                    # Get the values of the row
                    objects = row.values

                    # Create the node
                    g.add((subject_uri, A, COBIE[sheet]))

                    # Add objects
                    i = 0
                    for obj in objects:
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

                            g.add((subject_uri, COBIE[predicate], facility_uri + "/" + target_sheet.lower() + "/" + self.create_uri(obj)))
                        elif sheet == "Component" and predicate == "space":
                            # Split by "," to get all spaces and remove whitespace
                            spaces = [space.strip() for space in obj.split(",")]
                            for space in spaces:
                                g.add((subject_uri, COBIE[predicate], facility_uri + "/" + "space" + "/" + self.create_uri(space)))
                        else:
                            g.add((subject_uri, COBIE[predicate], Literal(str(obj).replace('"', '\\"'))))
                        i += 1      

            # Create the attributes
            print("Processing Attribute sheet...")
            for _, row in df['Attribute'].iterrows():
                target_sheet = row['SheetName']
                target_row_name = row['RowName']
                target_uri = facility_uri + "/" + target_sheet.lower() + "/" + self.create_uri(target_row_name)

                attribute_uri = target_uri + "/attribute/" + self.create_uri(row['Name'])

                g.add((attribute_uri, A, COBIE['Attribute']))
                g.add((attribute_uri, COBIE['name'], Literal(row['Name'])))
                g.add((attribute_uri, COBIE['value'], Literal(row['Value'])))
                g.add((attribute_uri, COBIE['unit'], Literal(row['Unit'])))
                g.add((attribute_uri, COBIE['attributeTo'], target_uri))

            # Serialize the graph to a file
            graph_string = g.serialize(format='turtle', encoding='utf-8').decode()

            # Open the file and read it as a string, then upload it to the graph db
            blob_client = self.blob_store.upload_blob("cobie_graph_test_2.ttl", data=graph_string, overwrite=True)
            self.graph_db.import_rdf_data(blob_client.url)

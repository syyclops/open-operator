from openoperator.cobie_graph import CobieGraph
import pandas as pd

cobieGraph = CobieGraph()


def test_create_uri():
    assert cobieGraph.create_uri("Hello World") == "helloworld"
    assert cobieGraph.create_uri("!hello_world  %%!") == "helloworld"


def test_validate_spreadsheet():
    df = pd.read_excel("./invalid_cobie.xlsx", sheet_name=None)
    assert cobieGraph.validate_spreadsheet(df) == [
        "Empty or N/A cells found in column A of Component sheet.",
        "Not every record is linked to an existing Space."
    ]
    
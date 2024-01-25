import argparse
from openoperator import OpenOperator
from dotenv import load_dotenv
from rdflib import Namespace
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Upload a COBie file to the graph.')
    parser.add_argument('--file_path', type=str, help='The path to the file to upload')
    args = parser.parse_args()

    assert args.file_path, "Please provide a file path"

    operator = OpenOperator()

    file_path = args.file_path

    operator.cobie_graph.upload_spreadsheet(file_path, Namespace("https://example.com/"))


if __name__ == "__main__":
    main()
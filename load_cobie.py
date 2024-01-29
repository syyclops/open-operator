import argparse
from openoperator import OpenOperator
from dotenv import load_dotenv
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Upload a COBie file to the graph.')
    parser.add_argument('--file_path', type=str, help='The path to the file to upload')
    parser.add_argument('--namespace', type=str, help='The namespace to use for the graph', default="https://example.com/")
    args = parser.parse_args()

    operator = OpenOperator()

    with open(args.file_path, "rb") as file:
        file_content = file.read()
        operator.cobie.upload_spreadsheet(file_content, portfolio_namespace=args.namespace)

if __name__ == "__main__":
    main()
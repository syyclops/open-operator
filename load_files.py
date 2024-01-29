import argparse
from openoperator import OpenOperator
from dotenv import load_dotenv
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Upload a file to the assistant')
    parser.add_argument('--file_path', type=str, help='The path to the file to upload')
    args = parser.parse_args()

    assert args.file_path, "Please provide a file path"

    operator = OpenOperator()

    file_path = args.file_path

    with open(file_path, "rb") as file:
        file_content = file.read()
        file_name = file.name.split("/")[-1]

        operator.files.upload_file(file_content=file_content, file_name=file_name, portfolio_id="test", building_id="test10")


if __name__ == "__main__":
    main()
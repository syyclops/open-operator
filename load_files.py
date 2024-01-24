import argparse
from openoperator import OpenOperator
from dotenv import load_dotenv
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Upload a file to the assistant')
    parser.add_argument('--file_path', type=str, help='The path to the file to upload')
    args = parser.parse_args()

    assert args.file_path, "Please provide a file path"

    openoperator = OpenOperator()

    file_path = args.file_path

    openoperator.files.upload_file(file_path)


if __name__ == "__main__":
    main()
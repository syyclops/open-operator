from core.etl import etl



def main():
    file_path = "data/dunbar/documents/Dunbar HS Equipment List.pdf"

    etl.load_file(file_path)


if __name__ == "__main__":
    main()
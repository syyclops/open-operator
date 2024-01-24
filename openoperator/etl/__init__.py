from .etl import ETL
import os

etl = ETL(os.environ.get("UNSTRUCTURED_API_KEY"), os.environ.get("UNSTRUCTURED_URL"))
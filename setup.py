#!/usr/bin/env python3

from pathlib import Path
from setuptools import setup


directory = Path(__file__).resolve().parent
with open(directory / 'README.md', encoding='utf-8') as f:
  long_description = f.read()

setup(name='openoperator',
      version='0.0.1',
      description='AI Assistant for building operations and maintenance.',
      author='Anthony DeMattos',
      license='GPL-3.0',
      long_description_content_type='text/markdown',
      packages = ['openoperator', 'openoperator.llm', 'openoperator.blob_store', 'openoperator.vector_store', 'openoperator.document_loader', 
                  'openoperator.embeddings'],
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
      ],
      install_requires=[
        'openai',
        'neo4j',
        'fastapi',
        'uvicorn',
        'psycopg',
        'pydantic',
        'tiktoken',
        'unstructured-client',
        'rdflib',
        'pandas',
        'openpyxl',
        'azure-storage-blob',
        'pgvector',
        'python-multipart'
      ],
      python_requires='>=3.8',
      include_package_data=True,
      url="https://github.com/syyclops/open-operator",
    )
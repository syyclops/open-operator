#!/usr/bin/env python3

from pathlib import Path
from setuptools import setup


directory = Path(__file__).resolve().parent
with open(directory / 'README.md', encoding='utf-8') as f:
  long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='openoperator',
      version='0.0.1',
      description='AI Assistant for building operations and maintenance.',
      author='Anthony DeMattos',
      license='GPL-3.0',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages = ['openoperator'],
      classifiers=[
        "Programming Language :: Python :: 3"
      ],
      install_requires=requirements,
      python_requires='>=3.8',
      include_package_data=True,
      url="https://github.com/syyclops/open-operator",
    )
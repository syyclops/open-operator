<div align="center">
  <img height="400" src="./docs/assets/Futuristic%20Robot%20HVAC.png" style="border-radius: 8px;"/>

  <h3>

[Documentation](/docs) | [Examples](/examples) | [Community](https://github.com/syyclops/open-operator/discussions)

  </h3>

[![Unit Tests](https://github.com/syyclops/open-operator/actions/workflows/test.yml/badge.svg)](https://github.com/syyclops/open-operator/actions/workflows/test.yml)

</div>

## What is Open Operator?

Open Operator is a system that organizes and makes sense of the diverse operational data from buildings while adding a layer of analytics and engineering knowledge intelligence.

## Demo

https://github.com/syyclops/open-operator/assets/70538060/e9a833bd-b1e5-4a81-aef5-083f8b163144

## Installation

Install from source:

```
git clone https://github.com/syyclops/open-operator.git
cd open-opertor/
python3 -m pip install -e .
```

## Get started using the package locally

```
cp .env.example .env
export OPENAI_API_KEY=<your secret key>
export AZURE_STORAGE_CONNECTION_STRING=<your azure storage container>
export AZURE_CONTAINER_NAME=<your azure container name>
docker-compose.yml up -d
```

Then you can check out an example use of the package in [create_a_operator.ipynb](./examples/creating_a_operator.ipynb)

or

start a simple rest api [server](./examples/server.py)

## Useful Resources

1. [What is COBie?](https://www.thenbs.com/knowledge/what-is-cobie)
2. [Brick Schema](https://brickschema.org/)
3. [Data-Driven Smart Buildings: State-of-the-Art Review](https://github.com/syyclops/open-operator/files/14202864/Annex.81.State-of-the-Art.Report.final.pdf)

## License

This project is licensed under the MIT License - see the [License](./LICENSE) file for details.

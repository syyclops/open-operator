<div align="center">
  <img height="400" src="./docs/assets/Futuristic%20Robot%20HVAC.png" style="border-radius: 8px;"/>
</div>

## What is Open Operator?

Open Operator is a system that organizes and makes sense of the diverse operational data from buildings while adding a layer of analytics and engineering knowledge intelligence on top.

## Installation

Install from source:

```
git clone https://github.com/syyclops/open-operator.git
cd open-opertor/
python3 -m pip install -e .
```

## How to use locally

```
cp .env.example .env
export OPENAI_API_KEY=<your secret key>
export AZURE_STORAGE_CONNECTION_STRING=<your azure storage container>
export AZURE_CONTAINER_NAME=<your azure container name>
docker-compose.yml up -d
```

Then you can check out an example use of the package in [create_a_operator.ipynb](./notebooks/creating_a_operator.ipynb)

## Useful Resources

1. [What is COBie](https://www.thenbs.com/knowledge/what-is-cobie)
2. [what is Brick Schema](https://brickschema.org/)

## License

This project is licensed under the MIT License - see the [License](./LICENSE) file for details.

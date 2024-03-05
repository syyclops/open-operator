<div align="center">
  <img height="400" src="./docs/assets/Futuristic%20Robot%20HVAC.png" style="border-radius: 8px;"/>

  <h3>

[Documentation](https://syyclops.mintlify.app/getting-started/introduction) | [Examples](/examples) | [Community](https://github.com/syyclops/open-operator/discussions)

  </h3>

[![Unit Tests](https://github.com/syyclops/open-operator/actions/workflows/test.yml/badge.svg)](https://github.com/syyclops/open-operator/actions/workflows/test.yml)

</div>

## What is Open Operator?

Open Operator is a system that organizes and makes sense of the diverse operational data from buildings while adding a layer of analytics and engineering knowledge intelligence.

## Demo

https://github.com/syyclops/open-operator/assets/70538060/e9a833bd-b1e5-4a81-aef5-083f8b163144

## Project Structure

The project is organized within a single base directory named openoperator/, which contains all the components of the project:

- application/: Manages API endpoints, orchestrating the flow between the user and domain logic.
- domain/: The core layer where business logic lives. It includes:
  - model/: Defines the business entities and their behaviors.
  - repository/: Interfaces for data access and manipulation.
  - service/: Contains business operations and logic.
- infrastructure/: Supports the application with database access, external API communication, and other technical capabilities.
- utils.py: Utility functions used across the application.

## Domain-Driven Design (DDD)

The project aims to adhere to DDD principles as closely as possible, structuring the codebase to mirror real-world business scenarios and ensuring it remains aligned with business goals.

For those interested in learning more about DDD and its benefits, here are some resources:

["Domain-Driven Design: Tackling Complexity in the Heart of Software"](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf) by Eric Evans
["Implementing Domain-Driven Design"](https://dl.ebooksworld.ir/motoman/AW.Implementing.Domain-Driven.Design.www.EBooksWorld.ir.pdf) by Vaughn Vernon

## Installation

Install from source:

```
git clone https://github.com/syyclops/open-operator.git
cd open-opertor/
python3 -m pip install -e .
```

## Local Server Quickstart

1. Set the required environment variables:

```
cp .env.example .env
export OPENAI_API_KEY=<your secret key>
export AZURE_STORAGE_CONNECTION_STRING=<your azure storage container>
export AZURE_CONTAINER_NAME=<your azure container name>
export API_TOKEN_SECRET=<your api secret key>
```

2. Start the docker containers.

```
docker compose up -d
```

3. View the api docs at: http://localhost:8080/docs

## Useful Resources

1. [What is COBie?](https://www.thenbs.com/knowledge/what-is-cobie)
2. [Brick Schema](https://brickschema.org/)
3. [Data-Driven Smart Buildings: State-of-the-Art Review](https://github.com/syyclops/open-operator/files/14202864/Annex.81.State-of-the-Art.Report.final.pdf)

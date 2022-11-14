## IFC and [Brick Schema](https://brickschema.org/) Alignment

_Purpose_: Convert back and forth between ifc and brick files with ease

- Version Control
- Two way communcation

1. [Ifc Open Shell](https://blenderbim.org/docs-python/ifcopenshell-python/installation.html#) to extract data from the ifc file

2. [py-brickschema](https://github.com/BrickSchema/py-brickschema) to create the brick model (Turtle file)

## How to Run Locally

1. Place IFC files in ./files/brick_models/
   - Name them arch.ttl, mech.ttl, elec.ttl, plum.ttl
   - Or pass in the path where they are located using --archIfc, --mechIfc, etc.
2. Create venv (python3 -m venv venv)
3. Activate venv (. ./venv/bin/activate)
4. Install requirements (pip install -r requirements.txt)
5. Run: python3 ifc_to_brick.py --buildingUri example --buildingName example

### Docker Build and Exec

docker build . -t bim_and_bricks --platform linux/amd64

docker exec -it container_id python3 ifc_to_brick.py --buildingUri example --buildingName example

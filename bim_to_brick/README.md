## IFC to [Brick Schema](https://brickschema.org/) converter

1. Using [Ifc Open Shell](https://blenderbim.org/docs-python/ifcopenshell-python/installation.html#) to extract data from the ifc file

2. [py-brick](https://github.com/BrickSchema/py-brickschema) to create the brick model (Turtle file)

3. Sends the Turtle file to the server to be upload to Graph DB

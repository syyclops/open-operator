from typing import Union
from fastapi import FastAPI, File, UploadFile

import ifcopenshell
import ifcopenshell.util.element as Element
import aiofiles

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/ifcToBrick")
async def ifc_to_brick_model(file: UploadFile):
    # Save file to disk 
    file_location = f'files/{file.filename}'
    async with aiofiles.open(file_location, 'wb') as out_file:
        content = await file.read()  # async read
        await out_file.write(content)  # async write

    

    ifc = ifcopenshell.open(file_location)
    project = ifc.by_type("IfcProject")[0]
    site = project.IsDecomposedBy[0].RelatedObjects[0]
    building = site.IsDecomposedBy[0].RelatedObjects[0]
    return {"building": building}

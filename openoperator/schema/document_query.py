from pydantic import BaseModel


class DocumentQuery(BaseModel):
    query: str
    limit: int = 15
    file_url: str = None
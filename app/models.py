from pydantic import BaseModel

class SearchInput(BaseModel):
    city: str
    state: str
    country: str
    query: str

class Lead(BaseModel):
    name: str
    category: str | None = None
    phone: str | None = None
    address: str | None = None
    url: str | None = None

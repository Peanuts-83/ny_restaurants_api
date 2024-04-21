from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError, conlist


### Restaurant models #
class Grade(BaseModel):
    date: datetime
    grade: str
    # = Field(pattern='^[A-Z]$')
    score: int|None

class Address(BaseModel):
    building: str
    coord: list[float]
    street: str
    zipcode: str

class Restaurant(BaseModel):
    """
    By default, MongoDB _id field is not returned in the response body. If you want to include the _id field in the response body, you need to explicitly specify it in your query projection.
    ex: projection = {"_id": 1, "other_field": 1}
        cursor = collection.find(query, projection)
    """
    _id: ObjectId
    address: Address
    borough: str
    cuisine: str
    grades: list[Grade]
    name: str
    restaurant_id: str

### Neighnorhood models #
class Geometry(BaseModel):
    # use "constrained list" with conlist - not properly interpreted by pylance
    coordinates: conlist(conlist(conlist(float, min_length=2, max_length=2), min_length=1), min_length=1)  # type: ignore
    type: str

class Neighborhood(BaseModel):
    _id: ObjectId # _id is treated as private and not returned by fastapi
    id: str = None # _id processed on request
    geometry: Geometry
    name: str

### Point models #
class Point(BaseModel):
    longitude: float = Field(float, gte=-180, lte=180)
    latitude: float = Field(float, gte=-90, lte=90)



try:
    Restaurant()
    Neighborhood()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
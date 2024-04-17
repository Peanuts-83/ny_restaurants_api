from datetime import datetime
import typing
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError, conlist


### Restaurant models #
class Grade(BaseModel):
    date: datetime
    grade: str
    # = Field(pattern='^[A-Z]$')
    score: int

class Address(BaseModel):
    building: str
    coord: list[float]
    street: str
    zipcode: str

class Restaurant(BaseModel):
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
    _id: ObjectId
    geometry: Geometry
    name: str

try:
    Restaurant()
    Neighborhood()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
from datetime import datetime
import typing
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError


### Restaurant models #
class Grade(BaseModel):
    date: datetime
    grade: str = Field(pattern='^[A-F]$')
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
    grades: list[Grade]
    name: str
    restaurant_id: str

### Neighnorhood models #
class Geometry(BaseModel):
    coordinates: list[list[float]]
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
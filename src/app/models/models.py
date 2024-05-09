from datetime import datetime
from typing import Any, Dict
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
    coordinates: Any  # type: ignore
    type: str

class Neighborhood(BaseModel):
    _id: ObjectId # _id is treated as private and not returned by fastapi
    # id: str = None # _id processed on request
    geometry: Geometry
    name: str

### Geospatial models #
class Point(BaseModel):
    longitude: float = Field(float, gte=-180, lte=180)
    latitude: float = Field(float, gte=-90, lte=90)

class Distance(BaseModel):
    min: int
    max: int


### Utils models #
class SingleItemDict(BaseModel):
    val: Dict[str, Any]

def check_dict_length(arr):
    """
    Custom validator to ensure len(dict) == 1.
    """
    for v in arr:
        if len(v) != 1:
            raise ValueError("Dictionnary param must contain exactly one item.")
    return v


try:
    Restaurant()
    Neighborhood()
except ValidationError as exc:
    print(repr(exc.errors()[0]['type']))
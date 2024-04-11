from enum import Enum
from typing import Collection
from bson import ObjectId
from pydantic import BaseModel, Field
from starlette.applications import Starlette

### Request options #
class HttpParams(BaseModel):
    nbr: int = Field(default=None, ge=0)
    page_nbr: int = Field(default=None, ge=1)


### ENUMS #
# class DBcollection(Enum):
#     RESTAURANT = 'db_restaurants'
#     NEIGHBORHOOD = 'db_neighborhoods'

# class TypedApp(Starlette):
#     def __getitem__(self, key: str) -> Collection:
#         return self.state[key]

# def typed_db(db) -> TypedApp:
#     return db

### ObjectId mapper #
class IdMapper():
    def toObj(self, id: str) -> ObjectId:
        """
        Set a str to ObjectId (bson) format for mongodb request.
        """
        return ObjectId(id) if not isinstance(id, ObjectId) else id

    def toStr(self, id: ObjectId) -> str:
        """
        Set ObjectId to str.
        """
        return str(id)
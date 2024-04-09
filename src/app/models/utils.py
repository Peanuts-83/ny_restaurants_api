from enum import Enum
from typing import Collection
from pydantic import BaseModel, Field
from starlette.applications import Starlette

### Request options #
class HttpParams(BaseModel):
    nbr: int = Field(default=5, ge=0)
    page_nbr: int = Field(default=1, ge=1)


### ENUMS #
# class DBcollection(Enum):
#     RESTAURANT = 'db_restaurants'
#     NEIGHBORHOOD = 'db_neighborhoods'

# class TypedApp(Starlette):
#     def __getitem__(self, key: str) -> Collection:
#         return self.state[key]

# def typed_db(db) -> TypedApp:
#     return db
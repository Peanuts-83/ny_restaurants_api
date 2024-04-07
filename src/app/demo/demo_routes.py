from typing import Annotated
from fastapi import Body, Path, Query, APIRouter
from pydantic import BaseModel, Field

### Router #
router = APIRouter()

### Models #
"""
The input model needs to be able to have a password.
The output model should not have a password.
The database model would probably need to have a hashed password.
"""

class Item(BaseModel):
    name: str
    price: float
    description: str|None = Field(default=None, title='description of item', max_length=300)
    tax: float|None = None # not required

class Database(BaseModel):
    name: str = 'my_database'
    items: list[Item] = []

### demo_DB #

demo_db = Database()

### Routes #

@router.get('/demo')
def read_root():
    return {"Hello": "World"}

@router.get('/demo/items/{item_id:int}')
def read_item(
    item_id: Annotated[int, Path(title='The id of an item', ge=1)],
    q: str|None = Query(default=None, max_length=20,pattern='^[a-z]{2,5}$', deprecated=True),
    short: bool = True):
    result = {"item_id": item_id, "short_response": short}
    if q:
        result.update({"q": q})
    return result

@router.post('/demo/item/create', response_model=Item)
def create_item(item: Item, importance: Annotated[int, Body(title='Level of hurry')] = 10) -> Item: # body arg in request > importance: 10
# def create_item(item: Annotated[Item, Body(embed=True)]): # body with item: {} instead of item as body
# def create_item(item: Item, importance: int=10): # query arg in path > ?importance=10
    demo_db.items.append(item)
    return item
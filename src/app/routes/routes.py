from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Body, status, Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from models.models import Restaurant, Neighborhood


router = APIRouter()

### Request options #
class HttpParams(BaseModel):
    nbr: int = Field(default=5, ge=0)
    page_nbr: int = Field(default=1, ge=1)

@router.post('/',
            response_description='get first restaurant in the list',
            status_code=status.HTTP_200_OK,
            response_model=Restaurant)
def read_one_restaurant(request: Request, params: Annotated[HttpParams, Body(embed=True)] = HttpParams()):
    """
    TEST for getting one restaurant
    """
    return request.app.db_restaurants.find_one({})


@router.post('/liste',
            response_description='get list of restaurants',
            status_code=status.HTTP_200_OK,
            response_model=list[Restaurant])
def read_list_restaurants(request: Request, params: Annotated[HttpParams, Body(embed=True)] = HttpParams()):
    """
    GET RESTAURANTS LIST

    Args:
        params(HttpParams): required.
            nbr(int): number of items required.
            page_nbr(int): page number.

    Returns:
        list[Restaurant]: the requested list with idObject as str.
    """
    skip = (params.page_nbr - 1) * params.nbr
    query = {}
    if params.page_nbr>1:
        restaurants_cursor: list[dict] = request.app.db_restaurants.find(query).skip(skip).limit(params.nbr)
    else:
        restaurants_cursor: list[dict] = request.app.db_restaurants.find(query).limit(params.nbr)
    # idObject to str
    result = [{**rest, '_id': str(rest['_id'])} for rest in restaurants_cursor]
    return list(result)

@router.post('/create',
            response_description='create a restaurant',
            status_code=status.HTTP_201_CREATED,
            response_model=Restaurant)
def create_restaurant(request: Request, restaurant: Annotated[Restaurant, Body(embed=True)], params: Annotated[HttpParams, Body(embed=True)] = HttpParams(nbr=1) ):
    """
    CREATE A RESTAURANT

    Args:
        restaurant(Restaurant): restaurant data.
        params(HttpParams): not used actually.

    Returns:
        created restaurant.
    """
    restaurant = jsonable_encoder(restaurant)
    new_restaurant = request.app.db_restaurants.insert_one(restaurant)
    created_restaurant = request.app.db_restaurants.find_one(
        {"_id": ObjectId(new_restaurant.inserted_id)}
    )
    return created_restaurant
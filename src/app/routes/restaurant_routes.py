import logging
from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Body, status, Request, Response
from fastapi.encoders import jsonable_encoder
from pymongo.collection import Collection

from ..models.utils import HttpParams
from ..models.models import Restaurant

### RESTAURANT_ROUTER
rest_router = APIRouter()

@rest_router.post('/',
            response_description='get first restaurant in the list',
            status_code=status.HTTP_200_OK,
            response_model=Restaurant)
def read_one_restaurant(request: Request, params: Annotated[HttpParams, Body(embed=True)] = HttpParams(nbr=1)):
    """
    TEST for getting one restaurant
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_restaurants
    return coll.find_one({})


@rest_router.post('/liste',
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
    coll: Collection = request.app.db_restaurants
    skip = (params.page_nbr - 1) * params.nbr
    query = {}
    if params.page_nbr>1:
        restaurants_cursor: list[dict] = coll.find(query).skip(skip).limit(params.nbr)
    else:
        restaurants_cursor: list[dict] = coll.find(query).limit(params.nbr)
    # idObject to str
    result = [{**rest, '_id': str(rest['_id'])} for rest in restaurants_cursor]
    return list(result)


@rest_router.post('/create',
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
    coll: Collection = request.app.db_restaurants
    restaurant = jsonable_encoder(restaurant)
    try:
        new_restaurant = coll.insert_one(restaurant)
        created_restaurant = coll.find_one(
            {"_id": ObjectId(new_restaurant.inserted_id)}
        )
        return created_restaurant
    except Exception as e:
        print(f'Error on CREATE!', e)


@rest_router.delete('/delete/{id_neighb: int}',
                        response_description='delete a restaurant',
                        status_code=status.HTTP_200_OK,
                        response_model=int)
def delete_restaurant(request: Request, id_rest: Annotated[str, Body(embed=True)]):
    """
    DELETE A RESTAURANT

    Args:
        id_rest(str): id of restaurant.

    Returns:
        params(HttpParams)
        the deleted restaurant.
    """
    coll: Collection = request.app.db_restaurants
    # convert id if needed
    objectId = ObjectId(id_rest) if not isinstance(id_rest, ObjectId) else id_rest
    result = coll.delete_one({'_id': objectId})
    if result.deleted_count==1:
        logging(f'Success - Neighborhood #{id_rest} DELETED')
        return id_rest
    else:
        logging(f'Neighborhood #{id_rest} not found!')
        return 0

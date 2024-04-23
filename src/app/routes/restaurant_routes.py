from typing import Annotated, Any, Dict, List
from fastapi import APIRouter, Body, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BeforeValidator
from pymongo.collection import Collection


from ..middleware.http_params import OP_FIELD, HttpParams, Filter
from ..models.models import Restaurant, check_dict_length

### RESTAURANT_ROUTER
rest_router = APIRouter()


@rest_router.post(
    "/",
    response_description="get first restaurant in the list",
    status_code=status.HTTP_200_OK,
    response_model=Restaurant,
)
def read_one_restaurant(
    request: Request, params: Annotated[HttpParams, Body(embed=True)] = HttpParams()
):
    """
    TEST for getting one restaurant
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_restaurants
    return coll.find_one({})


@rest_router.post(
    "/list",
    response_description="get list of restaurants",
    status_code=status.HTTP_200_OK,
    response_model=list[Restaurant],
)
def read_list_restaurants(
    request: Request,
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(
        nbr=5,
        page_nbr=1,
        filters={
            "value": "Wendy'S",
            "operator_field": OP_FIELD.CONTAIN,
            "field": "name",
        },
    ),
):
    """
    GET RESTAURANTS LIST

    Args:
        params(HttpParams): required.
            nbr(int): number of items required.
            page_nbr(int): page number.
            filters(Filter): filters for request.

    Returns:
        list[Restaurant]: the requested list.
    """
    coll: Collection = request.app.db_restaurants
    skip = (params.page_nbr - 1) * params.nbr
    query = Filter(**params.filters).make()
    if params.page_nbr > 1:
        restaurants_cursor: list[dict] = coll.find(query).skip(skip).limit(params.nbr)
    else:
        restaurants_cursor: list[dict] = coll.find(query).limit(params.nbr)
    result = list(restaurants_cursor)
    print(f"Mongodb request: {query}")
    return result


@rest_router.post(
    "/create",
    response_description="create a restaurant",
    status_code=status.HTTP_201_CREATED,
    response_model=Restaurant,
)
def create_restaurant(
    request: Request, restaurant: Annotated[Restaurant, Body(embed=True)]
):
    """
    CREATE A RESTAURANT

    Args:
        restaurant(Restaurant): restaurant data.

    Returns:
        created restaurant.
    """
    coll: Collection = request.app.db_restaurants
    restaurant = jsonable_encoder(restaurant)
    new_restaurant = coll.insert_one(restaurant)
    created_restaurant = coll.find_one({"_id": new_restaurant.inserted_id})
    return created_restaurant


@rest_router.put(
    "/update/",
    response_description="update a restaurant",
    status_code=status.HTTP_200_OK,
    response_model=Restaurant,
)
def update_restaurant(
    request: Request,
    id: Annotated[str, Body(embed=True)],
    changes: Annotated[dict, Body(embed=True)],
):
    """
    UPDATE A RESTAURANT

    Args:
        changes(dict): {restaurant_id, changed_elements}.

    Returns:
        the updated neighborhood.
    """
    coll: Collection = request.app.db_restaurants
    result = coll.update_one({"restaurant_id": id}, {"$set": changes})
    if result.matched_count < 1:
        raise HTTPException(
            status_code=404, detail=f"No match with restaurant_id {id}."
        )
    confirm = coll.find_one(
        {
            "restaurant_id": (
                changes["restaurant_id"] if hasattr(changes, "restaurant_id") else id
            )
        }
    )
    return confirm


@rest_router.put("/update/field/name/", response_description="change field name")
def update_restaurants_field(
    request: Request,
    field: Annotated[str, Body(embed=True)],
    new_field: Annotated[str, Body(embed=True)],
):
    """
    FOR DATABASE MANAGMENT ONLY!
    Change a field name

    returns nbr of items processed.
    """
    coll = request.app.db_restaurants
    cursor = coll.update_many(
        {field: {"$exists": True}}, {"$rename": {field: new_field}}
    )
    return f"Items processed: {cursor.matched_count}"


@rest_router.put("/update/field/set/", response_description="set field value")
def update_restaurants_value(
    request: Request,
    field: Annotated[str, Body(embed=True)],
    values: Annotated[List[Dict[str, Any]], Body(embed=True)],
):
    """
    FOR DATABASE MANAGMENT ONLY!
    Set a field value and creates the field if needed.
    values:
        {field: value}[] : only one item supported for each value.

    return {<field>: number_of_items_processed}
    """
    coll = request.app.db_restaurants
    result = {}
    for value in values:
        if len(value) > 1:
            raise HTTPException(
                status_code=422,
                detail=f"Each value should contain only one item. Error value: {value}",
            )
        cursor = coll.update_many({field: {"$exists": True}}, {"$set": value})
        result[list(value.keys())[0]] = cursor.matched_count
    return f"Items processed: {result}"


@rest_router.delete("/update/field/unset/", response_description="delete a field")
def delete_restaurant_field(
    request: Request,
    field: Annotated[str, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)] = None,
):
    """
    FOR DATABASE MANAGMENT ONLY!
    Unset a field of a collection.
    params:
        field<str> : target fiel to unset - Required.
        params.filters<Filter>: Base filter for HttpParams - Optional.

    return {<field>: number_of_items_processed}
    """
    coll = request.app.db_restaurants
    query = {}
    if params.filters and len(params.filters) > 0:
        query = Filter(**params.filters).make()
    print(query, {"$unset": field})
    result = coll.update_many(query, {"$unset": {field: ""}})
    if result.modified_count > 0:
        return {field: result.modified_count}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No item modified for field {field} and filters {params.filters}.",
        )


@rest_router.delete(
    "/delete",
    response_description="delete a restaurant",
    status_code=status.HTTP_200_OK,
)
def delete_restaurant(request: Request, id: Annotated[str, Body(embed=True)]):
    """
    DELETE A RESTAURANT

    Args:
        id(str): restaurant_id.

    Returns:
        params(HttpParams)
        the deleted restaurant.
    """
    coll: Collection = request.app.db_restaurants
    result = coll.delete_many({"restaurant_id": id})
    if result.deleted_count > 0:
        return {"restaurant_id": id, "deleted_nbr": result.deleted_count}
    else:
        raise HTTPException(status_code=404, detail=f"Restaurant #{id} not found!")

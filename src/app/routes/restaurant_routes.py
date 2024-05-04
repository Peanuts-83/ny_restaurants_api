from typing import Annotated, Any, Dict, List
from fastapi import APIRouter, Body, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BeforeValidator
from pymongo.collection import Collection


from ..middleware.http_params import (
    OP_FIELD,
    HttpParams,
    Filter,
    Sort,
    httpParamsInterpreter,
)
from ..models.models import Restaurant, check_dict_length

### RESTAURANT_ROUTER
rest_router = APIRouter()


@rest_router.post(
    "/one",
    response_description="get first restaurant in the list",
    status_code=status.HTTP_200_OK,
    response_model=Restaurant,
)
def read_one_restaurant(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    GET ONE RESTAURANT

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n


    @return:\n
        Restaurant: the one asked for.\n
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_restaurants
    query = Filter(**params.filters).make()
    result = coll.find_one(query)
    return result


@rest_router.post(
    "/list",
    response_description="get list of restaurants",
    status_code=status.HTTP_200_OK,
    response_model=list[Restaurant],
)
def read_list_restaurants(
    request: Request,
    params: Annotated[HttpParams, Body(embed=True)]
):
    """
    GET RESTAURANTS LIST

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        list[Restaurant]: the requested list.\n
    """
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    query = Filter(**params.filters).make()
    cursor: list[dict] = coll.find(query).sort(sort["field"], sort["way"]).skip(skip).limit(limit)
    result = list(cursor)
    return result


@rest_router.post(
    "/distinct",
    response_description="get all distinct <field>",
    status_code=status.HTTP_200_OK,
    response_model=list[str],
)
def get_distinct_field(
    request: Request,
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(
        sort=("name", Sort.ASC)
    ),
):
    """
    GET DISTINCT VALUES OF A FIELD

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): no filters used.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        list[str]: a list of names<str>.\n
    """
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    #  params.sort tuple must be properly set
    if params.sort[0] is None or params.sort[0]=="":
        raise HTTPException(status_code=422, detail=f"Sort field is not properly defined: {sort['field']} \nfrom {params.sort}")
    if params.sort[1] is None or not isinstance(params.sort[1], Sort):
        raise HTTPException(status_code=422, detail=f"Sort way is not properly defined: {sort['way']} \nfrom {params.sort}")
    cursor = coll.aggregate(
        [
            {
                "$group": {"_id": f"${sort['field']}"}
            },  # group by field to get distinct names
            {"$sort": {"_id": sort['way']}},  # order alphabetically A > Z
            {"$skip": skip},
            {"$limit": limit},
        ]
    )
    result = list(cursor)
    # return list of values<str>
    return list(map(lambda x: x["_id"], result))


@rest_router.post(
    "/create",
    response_description="create a restaurant",
    status_code=status.HTTP_201_CREATED,
    response_model=Restaurant,
)
def create_restaurant(
    request: Request,
    restaurant: Annotated[Restaurant, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    CREATE A RESTAURANT

    @param restaurant:\n
        Restaurant: datas for new restaurant.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        Restaurant: created restaurant.
    """
    coll: Collection = request.app.db_restaurants
    restaurant = jsonable_encoder(restaurant)
    new_restaurant = coll.insert_one(restaurant)
    created_restaurant = coll.find_one({"_id": new_restaurant.inserted_id})
    return created_restaurant


@rest_router.put(
    "/update",
    response_description="update a restaurant",
    status_code=status.HTTP_200_OK,
    response_model=Restaurant,
)
def update_restaurant(
    request: Request,
    id: Annotated[str, Body(embed=True)],
    changes: Annotated[dict, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    UPDATE A RESTAURANT

    @param id:\n
        str: restaurant's id.\n

    @param changes:\n
        Dictionnary: {changed_elements}.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        Restaurant: the updated restaurant.
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


@rest_router.put("/update/field/name", response_description="change field name")
def update_restaurants_field(
    request: Request,
    field: Annotated[str, Body(embed=True)],
    new_field: Annotated[str, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    FOR DATABASE MANAGMENT ONLY! Change a field name.

    @param field:\n
        str: field name to be changed.\n

    @param new_field:\n
        str: new name for the field.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        {field, new_field, nbr of items processed}.
    """
    coll = request.app.db_restaurants
    skip, limit = httpParamsInterpreter(params)
    cursor = (
        coll.update_many({field: {"$exists": True}}, {"$rename": {field: new_field}})
        .skip(skip)
        .limit(limit)
    )
    result = {
        "field": field,
        "new field": new_field,
        "nbr of results": cursor.matched_count,
    }
    return f"Items processed: result"


@rest_router.put("/update/field/set", response_description="set field value")
def update_restaurants_value(
    request: Request,
    field: Annotated[str, Body(embed=True)],
    values: Annotated[List[Dict[str, Any]], Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    FOR DATABASE MANAGMENT ONLY! Set a field value and create the field if needed.

    @param field:\n
        str: field to be changed.\n

    @param values:\n
        {key<str>: value<any>}[] : only one item supported for each value.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
       {field: number of items processed}[]
    """
    coll = request.app.db_restaurants
    skip, limit = httpParamsInterpreter(params)
    result = {}
    for value in values:
        if len(value) > 1:
            raise HTTPException(
                status_code=422,
                detail=f"Each value should contain only one item. Error value: {value}",
            )
        cursor = (
            coll.update_many({field: {"$exists": True}}, {"$set": value})
            .skip(skip)
            .limit(limit)
        )
        result[list(value.keys())[0]] = cursor.matched_count
    return f"Items processed: {result}"


@rest_router.delete("/update/field/unset", response_description="delete a field")
def delete_restaurant_field(
    request: Request,
    field: Annotated[str, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)] = None,
):
    """
    FOR DATABASE MANAGMENT ONLY! Unset a field of a collection.

    @param field:\n
        str : target field to unset.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        {<field>: number_of_items_processed}
    """
    coll = request.app.db_restaurants
    skip, limit = httpParamsInterpreter(params)
    query = {}
    if params.filters and len(params.filters) > 0:
        query = Filter(**params.filters).make()
    result = coll.update_many(query, {"$unset": {field: ""}}).skip(skip).limit(limit)
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
def delete_restaurant(
    request: Request,
    id: Annotated[str, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    DELETE A RESTAURANT by retaurant_id.

    @param id:\n
        str: restaurant_id.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        {restaurant_id: str, deleted_nbr: int}
    """
    coll: Collection = request.app.db_restaurants
    result = coll.delete_many({"restaurant_id": id})
    if result.deleted_count > 0:
        return {"restaurant_id": id, "deleted_nbr": result.deleted_count}
    else:
        raise HTTPException(status_code=404, detail=f"Restaurant #{id} not found!")

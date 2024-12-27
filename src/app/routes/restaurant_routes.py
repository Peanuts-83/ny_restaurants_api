import json
from typing import Annotated, Any, Dict, List
from fastapi import APIRouter, Body, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from pymongo.collection import Collection

from ..middleware.cursor_middleware import cursor_to_object


from ..middleware.http_params import (
    OP_FIELD,
    HttpParams,
    Filter,
    SortWay,
    httpParamsInterpreter,
)
from ..models.models import ListResponse, Restaurant

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
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n


    @return:\n
        Restaurant: the one asked for.\n
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    if params.filters and params.filters != {}:
        query = Filter(**params.filters).make()
    l_aggreg = []
    try:
        l_aggreg.insert(0, query)
    except:
        pass
    sort and l_aggreg.append({"$sort": sort})
    skip and l_aggreg.append({"$skip": skip})
    l_aggreg.append({"$limit": 1})
    cursor = coll.aggregate(l_aggreg)
    # Aggregation pipes return list
    return list(cursor)[0]


@rest_router.post(
    "/list",
    response_description="get list of restaurants",
    status_code=status.HTTP_200_OK,
    response_model=ListResponse,
)
def read_list_restaurants(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    GET RESTAURANTS LIST

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        list[Restaurant]: the requested list.\n
    """
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    if not limit:
        limit = 30
    if params.filters and params.filters != {}:
        query = Filter(**params.filters).make()

    l_aggreg = [{"$match": {"name": {"$ne": ""}}}]

    try:
        l_aggreg.append(query)
    except:
        pass
    sort and l_aggreg.append({"$sort": sort})
    skip and l_aggreg.append({"$skip": skip})
    limit and l_aggreg.append({"$limit": limit})
    cursor = coll.aggregate(l_aggreg)
    return {"data": cursor, "page_nbr": params.page_nbr}


@rest_router.post(
    "/distinct",
    response_description="get all distinct <field>",
    status_code=status.HTTP_200_OK,
    response_model=ListResponse,
)
def get_distinct_field(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    GET DISTINCT VALUES OF A FIELD from Restaurants collection.

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): no filters used.\n
        sort(SortParams{field:str, way:1|-1}): use field for distinct values - ascending order by default.\n

    @return:\n
        list[str]: a list of names<str>.\n
    """
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    if params.filters and params.filters != {}:
        query = Filter(**params.filters).make()

    # distinct values check
    distinctField = list(sort.keys())[0]
    distinctWay = sort[distinctField]
    if distinctField is None or distinctField == "":
        raise HTTPException(
            status_code=422,
            detail=f"Sort field is not properly defined: {distinctField} from {sort}",
        )
    if distinctWay is None:
        raise HTTPException(
            status_code=422,
            detail=f"Sort way is not properly defined: {distinctWay} from {sort}",
        )

    # start building aggregation pipeline
    l_aggreg = [
        {"$match": {distinctField: {"$ne": ""}}},  # no empty field allowed
        {
            "$group": {
                "_id": f"${distinctField}",  # group by field to get distinct names
                "name": {"$addToSet": f"${distinctField}"}
            }
        },
    ]

    # additionnal values for restaurant name request
    l_name_options = {
                "borough": {"$addToSet": "$borough"},
                "cuisine": {"$addToSet": "$cuisine"},
                "street": {"$addToSet": "$address.street"},
                "coord": {"$addToSet": "$address.coord"}}
    if distinctField == 'name':
        l_aggreg[1]["$group"] = {**l_aggreg[1]["$group"],**l_name_options}

    # complete aggregation pipeline
    try:
        l_aggreg.insert(1,query)
    except:
        pass
    sort and l_aggreg.append(
        {"$sort": {"_id": list(sort.values())[0]}}
    )  # _id is the right target after $group stage
    skip and l_aggreg.append({"$skip": skip})
    limit and l_aggreg.append({"$limit": limit})
    cursor = coll.aggregate(l_aggreg)
    result = list(cursor_to_object(cursor))
    return {"data": list(map(lambda d: {k:v[0] for k,v in d.items()}, result)), "page_nbr": params.page_nbr}


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
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

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
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        Restaurant: the updated restaurant.
    """
    coll: Collection = request.app.db_restaurants
    result = coll.update_one({"restaurant_id": id}, {"$set": changes})
    if result.matched_count == 0:
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
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        {field, new_field, nbr of items processed}.
    """
    coll = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    # update_many(filter<{'name':'Wendys'}>, update<{field:{'$exists':True}},{"$rename": {field: new_field}})
    if params.filters and len(params.filters) > 0:
        query = Filter(**params.filters).make()
    l_aggreg = [{field: {"$exists": True}}, {"$rename": {field: new_field}}]
    query and l_aggreg.insert(0, query["$match"])
    skip and l_aggreg.append(skip)
    limit and l_aggreg.append(limit)
    cursor = coll.update_many(*l_aggreg)
    if cursor.modified_count > 0:
        return {
            "new_field": new_field,
            "matched": cursor.matched_count,
            "modified": cursor.modified_count,
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No field modified for new field {new_field} and filters {params.filters}.",
        )


@rest_router.put("/update/field/set", response_description="set field value")
def update_restaurants_value(
    request: Request,
    new_item: Annotated[dict[str, Any], Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    FOR DATABASE MANAGMENT ONLY! Set a field value and create the field if needed.

    @param new_item:\n
        {field_name<str>: value<any>} : field name and it's value.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
       {field: number of items processed}[]
    """
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    # update_many(filter<{'name':'Wendys'}>, update<{$set:{'cuisine':'BUDU'}}, upsert<Bool: insert if not present>>)
    if params.filters and len(params.filters) > 0:
        query = Filter(**params.filters).make()
    l_aggreg = [{"$set": new_item}]
    query and l_aggreg.insert(0, query["$match"])
    skip and l_aggreg.append(skip)
    limit and l_aggreg.append(limit)
    cursor = coll.update_many(*l_aggreg, upsert=True)
    if cursor.modified_count > 0:
        return {
            "new_value": new_item,
            "matched": cursor.matched_count,
            "modified": cursor.modified_count,
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No item modified for new item {new_item} and filters {params.filters}.",
        )


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
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        {<field>: number_of_items_processed}
    """
    coll = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    if params.filters and len(params.filters) > 0:
        query = Filter(**params.filters).make()
    l_aggreg = [{"$unset": {field: ""}}]
    query and l_aggreg.insert(0, query["$match"])
    skip and l_aggreg.append(skip)
    limit and l_aggreg.append(limit)
    # update_many(filter<{'name':'Wendys'}>, update<{$unset:{'cuisine':''}})
    cursor = coll.update_many(*l_aggreg)
    if cursor.modified_count > 0:
        return {
            "field": field,
            "matched": cursor.matched_count,
            "modified": cursor.modified_count,
        }
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
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        {restaurant_id: str, deleted_nbr: int}
    """
    coll: Collection = request.app.db_restaurants
    result = coll.delete_many({"restaurant_id": id})
    if result.deleted_count > 0:
        return {"restaurant_id": id, "deleted_nbr": result.deleted_count}
    else:
        raise HTTPException(status_code=404, detail=f"Restaurant #{id} not found!")

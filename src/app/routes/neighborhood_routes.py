from typing import Annotated, Any
from fastapi import APIRouter, Body, HTTPException, status, Request
from pymongo.collection import Collection

from ..middleware.cursor_middleware import cursor_to_object

from ..middleware.http_params import (
    OP_FIELD,
    Filter,
    HttpParams,
    SortParams,
    httpParamsInterpreter,
)
from ..models.utils import IdMapper
from ..models.models import Neighborhood

# NEIGHBORHOOD_ROUTER
neighb_router = APIRouter(prefix="/neighborhood")


@neighb_router.post(
    "/one",
    response_description="get one neighborhood in the list",
    status_code=status.HTTP_200_OK,
    response_model=Neighborhood,
)
def read_one_neighborhood(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    TEST for getting one neighborhood

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_neighborhoods
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


@neighb_router.post(
    "/list",
    response_description="get list of neighborhoods",
    status_code=status.HTTP_200_OK,
    response_model=list[Neighborhood],
)
def read_list_neighborhoods(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    GET NEIGHBORHOODS LIST

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        list[Neighborhood]: the requested list.
    """
    coll: Collection = request.app.db_neighborhoods
    skip, limit, sort = httpParamsInterpreter(params)
    if params.filters and params.filters != {}:
        query = Filter(**params.filters).make()
    l_aggreg = []
    try:
        l_aggreg.append(query)
    except:
        pass
    sort and l_aggreg.append({"$sort": sort})
    skip and l_aggreg.append({"$skip": skip})
    limit and l_aggreg.append({"$limit": limit})
    cursor = coll.aggregate(l_aggreg)
    return cursor


@neighb_router.post(
    "/distinct",
    response_description="get all distinct neighborhoods",
    status_code=status.HTTP_200_OK,
    response_model=list[dict],
)
def get_distinct_neighborhood(
    request: Request,
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(
        sort=SortParams(field="name", way=1)
    ),
):
    """
    GET DISTINCT NEIGHBORHOOD NAMES

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        list[str]: list of names.
    """
    coll: Collection = request.app.db_neighborhoods
    skip, limit, sort = httpParamsInterpreter(params)
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
    l_aggreg = [
        {"$match": {distinctField: {"$ne": ""}}},  # no empty field allowed
        {
            "$group": {
                "_id": f"${distinctField}",  # group by field to get distinct names
                "coords": {"$addToSet": "$geometry.coordinates"},
                "name": {"$addToSet": "$name"},
            }
        },
    ]
    sort and l_aggreg.append(
        {"$sort": {"_id": list(sort.values())[0]}}
    )  # _id is the right target after $group stage
    skip and l_aggreg.append({"$skip": skip})
    limit and l_aggreg.append({"$limit": limit})
    cursor = coll.aggregate(l_aggreg)
    return list(cursor)


@neighb_router.put("/update/field/set", response_description="set field value")
def update_neighborhood_value(
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
    coll: Collection = request.app.db_neighborhoods
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



@neighb_router.put(
    "/update",
    response_description="update a neighborhood",
    status_code=status.HTTP_200_OK,
    response_model=Neighborhood,
)
def update_neighborhood(
    request: Request,
    name: Annotated[str, Body(embed=True)],
    changes: Annotated[dict, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    UPDATE A NEIGHBORHOOD

    @param name:\n
        str: neighborhood name.\n

    @param changes:\n
        dict: {changed_elements}.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        the updated neighborhood.
    """
    coll: Collection = request.app.db_neighborhoods
    result = coll.update_one({"name": name}, {"$set": changes})
    if result.matched_count == 0:
        raise HTTPException(
            status_code=404, detail={"update": {"error": f'name "{name}" not found'}}
        )
    confirm = coll.find_one({"name": name})
    return confirm

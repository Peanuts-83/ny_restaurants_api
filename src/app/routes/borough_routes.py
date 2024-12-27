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
from ..models.models import Borough, ListResponse, Point

# BOROUGH_ROUTER
borough_router = APIRouter(prefix="/borough")


@borough_router.post(
    "/one",
    response_description="get one borough in the list",
    status_code=status.HTTP_200_OK,
    response_model=Borough,
)
def read_one_borough(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    TEST for getting one borough

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_boroughs
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


@borough_router.post(
    "/list",
    response_description="get list of boroughs",
    status_code=status.HTTP_200_OK,
    response_model=ListResponse,
)
def read_list_boroughs(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    GET BOROUGHS LIST

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        list[Borough]: the requested list.
    """
    coll: Collection = request.app.db_boroughs
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


@borough_router.post(
    "/contain",
    response_description="check for coord's borough part of",
    status_code=status.HTTP_200_OK,
    # response_model=str
)
def borough_contain(
    request: Request,
    coord: Annotated[Point, Body(embed=True)]
):
    """
    FROM WHICH BOROUGH IS COORD

    @param coord
        longitude: float = Field(float, gte=-180, lte=180)
        latitude: float = Field(float, gte=-90, lte=90)

    @returns
        the corresponding borough
    """
    coll: Collection = request.app.db_boroughs
    point = {
        "type": "Point",
        "coordinates": [coord.longitude, coord.latitude]
    }
    cursor = coll.find_one({
        "geometry": {
            "$geoIntersects": { "$geometry": point}
        }
    })

    if cursor:
        return cursor_to_object(cursor)
    else:
        raise HTTPException(status_code=404, detail="No borough corresponding to given point")


@borough_router.put(
    "/update",
    response_description="update a borough",
    status_code=status.HTTP_200_OK,
    response_model=Borough,
)
def update_borough(
    request: Request,
    name: Annotated[str, Body(embed=True)],
    changes: Annotated[dict, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    UPDATE A BOROUGH

    @param name:\n
        str: borough name.\n

    @param changes:\n
        dict: {changed_elements}.\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n

    @return:\n
        the updated borough.
    """
    coll: Collection = request.app.db_boroughs
    result = coll.update_one({"name": name}, {"$set": changes})
    if result.matched_count == 0:
        raise HTTPException(
            status_code=404, detail={"update": {"error": f'name "{name}" not found'}}
        )
    confirm = coll.find_one({"name": name})
    return confirm

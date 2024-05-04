from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, status, Request
from pymongo.collection import Collection

from ..middleware.http_params import OP_FIELD, Filter, HttpParams, httpParamsInterpreter
from ..models.utils import IdMapper
from ..models.models import Neighborhood

# NEIGHBORHOOD_ROUTER
neighb_router = APIRouter(prefix="/neighborhood")


@neighb_router.post(
    "/one",
    response_description="get first neighborhood in the list",
    status_code=status.HTTP_200_OK,
    response_model=Neighborhood,
)
def read_one_neighborhood(
    request: Request, params: Annotated[HttpParams, Body(embed=True)] = HttpParams()
):
    """
    TEST for getting one neighborhood

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_neighborhoods
    query = Filter(**params.filters).make()
    result = coll.find_one(query)
    return result


@neighb_router.post(
    "/list",
    response_description="get list of neighborhoods",
    status_code=status.HTTP_200_OK,
    response_model=list[Neighborhood],
)
def read_list_neighborhoods(
    request: Request,
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(
        nbr=5,
        page_nbr=1,
        filters={
            "value": "Bedford",
            "operator_field": OP_FIELD.CONTAIN,
            "field": "name",
        },
    ),
):
    """
    GET NEIGHBORHOODS LIST

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        list[Neighborhood]: the requested list with idObject as str.
    """
    coll: Collection = request.app.db_neighborhoods
    projection = {"_id": 1, "geometry": 1, "name": 1}  # display _id Object
    skip, limit, sort = httpParamsInterpreter(params)
    query = Filter(**params.filters).make()
    neighborhoods_cursor: list[dict] = (
        coll.find(query, projection)
        .sort(sort["field"], sort["way"])
        .skip(skip)
        .limit(limit)
    )
    # id = idObject to str
    result = [
        {**neighb, "id": IdMapper().toStr(neighb["_id"])}
        for neighb in neighborhoods_cursor
    ]
    return result


@neighb_router.post(
    "/distinct",
    response_description="get all distinct neighborhoods",
)
def get_distinct_neighborhood(
    request: Request, params: Annotated[HttpParams, Body(embed=True)]
):
    """
    GET DISTINCT NEIGHBORHOOD NAMES

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(tuple[field<str>,Sort]): ascending order by default.\n

    @return:\n
        list[str]: list of names.
    """
    coll: Collection = request.app.db_neighborhoods
    skip, limit, sort = httpParamsInterpreter(params)
    # distinct() can't use skip & limit > aggregate used
    cursor = coll.aggregate(
        [
            {"$group": {"_id": f"${sort['field']}"}},  # group by name to get distinct names
            {"$sort": {"_id": sort['way']}},  # order alphabetically A > Z
            {"$skip": skip},
            {"$limit": limit},
        ]
    )
    result = list(cursor)
    # return list of values<str>
    return list(map(lambda x: x["_id"], result))


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
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(nbr=1, page_nbr=1),
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
        sort(tuple[field<str>,Sort]): ascending order by default.\n

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

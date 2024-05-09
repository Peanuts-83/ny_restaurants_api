from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from pymongo import GEOSPHERE
from pymongo.collection import Collection

from ..middleware.cursor_middleware import cursor_to_object

from ..models.models import Distance, Geometry, Neighborhood, Point, Restaurant

from ..middleware.http_params import (
    Filter,
    HttpParams,
    SortParams,
    httpParamsInterpreter,
)


point_router = APIRouter(prefix="/point")


@point_router.post(
    "/from_neighborhood",
    response_description="check for matching neighborhood.",
    status_code=status.HTTP_200_OK,
    response_model=Neighborhood,
)
def get_neighborhood(
    request: Request,
    coord: Annotated[Point, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)],
):
    """
    Get the corresponding neighborhood for a point coordinates [long, lat]

    @param coord:\n
        longitude <float[-180:180]>\n
        latitude <float[-90:90]>\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n
    """
    coll: Collection = request.app.db_neighborhoods
    result = coll.find_one(
        {
            "geometry": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [coord.longitude, coord.latitude],
                    }
                }
            }
        }
    )
    try:
        result = dict(result)
        return cursor_to_object(result)
    except:
        raise HTTPException(
            status_code=404, detail=f"No neighborhood match for coordinates {coord}."
        )


@point_router.post(
    "/to_restaurant",
    response_description="get nearest restaurants.",
    response_model=list[Restaurant],
)
def get_restaurants(
    request: Request,
    coord: Annotated[Point, Body(embed=True)],
    dist: Annotated[Distance, Body(embed=True)] = Distance(min=0, max=1000),
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(
        page_nbr=1, nbr=20, filters={}
    ),
):
    """
    Get the nearest restaurants from point coord, with distance min/max params.\n

    @param coord:\n
        longitude <float[-180:180]>\n
        latitude <float[-90:90]>\n

    @param dist:\n
        min <int> : distance in meters (default=0)\n
        max <int> : distance in meters (default=500)\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n
    """
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    if params.filters and len(params.filters) > 0:
        query = Filter(**params.filters).make() if params.filters else {}
    l_aggreg = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [coord.longitude, coord.latitude],
                },
                "minDistance": dist.min,
                "maxDistance": dist.max,
                "includeLocs": "address.coord",
                "distanceField": "dist.calculated",
                "spherical": True,
            }
        }
    ]
    # "longitude": -73.97474662218372,
    # "latitude": 40.76410978551795

    try:
        l_aggreg[0]["$geoNear"]["query"] = query["$match"]
    except:
        pass
    sort and l_aggreg.append({"$sort": sort})
    skip and l_aggreg.append({"$skip": skip})
    limit and l_aggreg.append({"$limit": limit})
    cursor = coll.aggregate(l_aggreg)
    result = list(cursor)
    return cursor_to_object(result)


@point_router.post(
    "/to_restaurant_within",
    response_description="get restaurants inside a shape determined by Points array.",
    response_model=list[Restaurant],
)
def get_restaurants_within(
    request: Request,
    shape: Annotated[Geometry, Body(embed=True)] = {
        "type": "Polygon",
        "coordinates": [
            [
                [-73.97608714333718, 40.76576475135964],
                [-73.9714531126955, 40.76362696209412],
                [-73.97018928615685, 40.76541377575056],
                [-73.97516033720885, 40.76736007167634],
                [-73.97608714333718, 40.76576475135964],
            ]
        ],
    },
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(
        page_nbr=1, nbr=20, filters={}
    ),
):
    """
    Get all the restaurants inside a shape of coordinates.\n

    @param shape:\n
        type: str\n
        coordinates: list[list[list[longitude <float[-180:180]>, latitude <float[-90:90]>]]]\n

    @param params:\n
        nbr(int): number of items required.\n
        page_nbr(int): page number.\n
        filters(Filter): filters for request.\n
        sort(SortParams{field:str, way:1|-1}): ascending order by default.\n
    """
    coll: Collection = request.app.db_restaurants
    skip, limit, sort = httpParamsInterpreter(params)
    if params.filters and len(params.filters) > 0:
        query = Filter(**params.filters).make() if params.filters else {}
    l_aggreg = [
        {
            "$match": {
                "address.coord": {
                    "$geoWithin": {
                        "$geometry": {"type": "Polygon", "coordinates": jsonable_encoder(shape.coordinates)}
                    }
                }
            }
        }
    ]
    try:
        l_key = list(query["$match"].keys())[0]
        l_value = list(query["$match"].values())[0]
        l_aggreg[0]["$match"][l_key] = l_value
    except:
        pass
    sort and l_aggreg.append({"$sort": sort})
    skip and l_aggreg.append({"$skip": skip})
    limit and l_aggreg.append({"$limit": limit})
    cursor = coll.aggregate(l_aggreg)
    result = list(cursor)
    return cursor_to_object(result)

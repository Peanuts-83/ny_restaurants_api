import json
from typing import Annotated, Any
from IPython import embed
from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from pymongo import GEOSPHERE
from pymongo.collection import Collection

from fastapi.routing import APIRoute

from ..models.utils import IdMapper

from ..models.models import Distance, Geometry, Neighborhood, Point, Restaurant

from ..middleware.http_params import Filter, HttpParams, httpParamsInterpreter


point_router = APIRouter(prefix="/point")


@point_router.post(
    "/from_neighborhood/",
    response_description="check for matching neighborhood.",
    status_code=status.HTTP_200_OK,
    response_model=Neighborhood,
)
def get_neighborhood(
    request: Request,
    coord: Annotated[Point, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(),
):
    """
    Get the corresponding neighborhood for a point coordinates [long, lat]

    @param coord:\n
        longitude <float[-180:180]>\n
        latitude <float[-90:90]>\n
    """
    # search on neighborhood collection
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
        # result = {**result, "id": IdMapper().toStr(result["_id"])}
        del result['_id']
        return result #
    except:
        raise HTTPException(
            status_code=404, detail=f"No neighborhood match for coordinates {coord}."
        )


@point_router.post(
    "/to_restaurant/",
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
    """
    coll: Collection = request.app.db_restaurants
    skip, limit = httpParamsInterpreter(params)
    cursor = (
        coll.find(
            {
                "address.coord": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [coord.longitude, coord.latitude],
                        },
                        "$minDistance": dist.min,
                        "$maxDistance": dist.max,
                    }
                }
            }
        ).skip(skip).limit(limit)
    )
    return list(cursor)


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
                [-73.97608714333718, 40.76576475135964]
            ]
        ]
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
    """
    coll: Collection = request.app.db_restaurants
    skip, limit = httpParamsInterpreter(params)
    cursor = coll.find({"address.coord": {"$geoWithin": {"$geometry": jsonable_encoder(shape)}}}).skip(skip).limit(limit)
    result = list(cursor)
    return result

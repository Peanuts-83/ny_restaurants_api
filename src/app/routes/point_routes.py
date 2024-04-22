import json
from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Request, status
from pymongo import GEOSPHERE
from pymongo.collection import Collection

from fastapi.routing import APIRoute

from ..models.utils import IdMapper

from ..modules.point.geospatial import doCreate2dSphere
from ..models.models import Distance, Neighborhood, Point, Restaurant

from ..middleware.http_params import Filter, HttpParams


point_router = APIRouter(prefix='/point')

@point_router.post('/from_neighborhood/',
            response_description='check for matching neighborhood.',
            status_code=status.HTTP_200_OK,
            response_model=Neighborhood )
def get_neighborhood(request: Request, coord:Annotated[Point, Body(embed=True)], params: Annotated[HttpParams, Body(embed=True)] = HttpParams()):
    """
    Get the corresponding neighborhood for a point coordinates [long, lat]
    coord:
        longitude <float[-180:180]>
        latitude <float[-90:90]>
    """
    # search on neighborhood collection
    coll: Collection = request.app.db_neighborhoods
    doCreate2dSphere(coll, "geometry")
    result = coll.find_one({
        "geometry": {
            "$geoIntersects": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [
                        coord.longitude,
                        coord.latitude
                    ]
                }
            }
        }
    })
    try:
        result
        return {**result, 'id': IdMapper().toStr(result['_id'])}
    except:
        raise HTTPException(status_code=404, detail=f"No neighborhood match for coordinates {coord}.")



@point_router.post('/to_restaurant/',
            response_description='get nearest restaurants.',
            response_model=list[Restaurant])
def get_restaurants(request:Request, coord: Annotated[Point, Body(embed=True)], dist: Annotated[Distance, Body(embed=True)] = Distance(min=0,max=1000), params: Annotated[HttpParams, Body(embed=True)] = HttpParams(page_nbr=1, nbr=20, filters={})):
    """
    Get the nearest restaurants from point coord, with distance min/max params.
    coord:
        longitude <float[-180:180]>
        latitude <float[-90:90]>
    dist:
        min <int> : distance in meters (default=0)
        max <int> : distance in meters (default=500)
    """
    coll: Collection = request.app.db_restaurants
    if (hasattr(params, 'page_nbr') and hasattr(params, 'nbr')) and (params.page_nbr!=None and params.nbr!=None):
        skip = (params.page_nbr - 1) * params.nbr
    else:
        skip = 0
        params.nbr=0
    doCreate2dSphere(coll, 'address.coordinates')
    if params.page_nbr>1:
        cursor = coll.find({
            "address.coordinates": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates":[coord.longitude, coord.latitude]},
                    "$minDistance": dist.min,
                    "$maxDistance": dist.max
                }
            }
        }).skip(skip).limit(params.nbr if hasattr(params, 'nbr') else 0)
    else:
        cursor = coll.find({
            "address.coordinates": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates":[coord.longitude, coord.latitude]},
                    "$minDistance": dist.min,
                    "$maxDistance": dist.max
                }
            }
        }).limit(params.nbr)

    # result = [{**item, 'id': IdMapper().toStr(item._id)} for item in list(cursor)]
    result = list(cursor)
    return result
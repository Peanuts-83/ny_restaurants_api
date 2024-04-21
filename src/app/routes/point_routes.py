from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Request, status
from pymongo.collection import Collection

from fastapi.routing import APIRoute

from ..models.utils import IdMapper

from ..modules.point.geospatial import doCreate2dSphere
from ..models.models import Neighborhood, Point

from ..middleware.http_params import HttpParams


point_router = APIRouter(prefix='/point')
geoIndex = None

@point_router.post('/from_neighborhood/',
            response_description='check for matching neighborhood.',
            status_code=status.HTTP_200_OK,
            response_model=Neighborhood )
def get_neighborhood(request: Request, coord:Annotated[Point, Body(embed=True)], params: Annotated[HttpParams, Body(embed=True)] = HttpParams()):
    """
    Get the corresponding neighborhood for a point coordinates [long, lat]
        longitude <float[-180:180]>
        latitude <float[-90:90]>
    """
    # search on neighborhood collection
    coll: Collection = request.app.db_neighborhoods
    try:
        geoIndex
    except:
        geoIndex = doCreate2dSphere(coll, "geometry")
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
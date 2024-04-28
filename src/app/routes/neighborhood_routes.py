from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, status, Request
from pymongo.collection import Collection

from ..middleware.http_params import OP_FIELD, Filter, HttpParams
from ..models.utils import IdMapper
from ..models.models import Neighborhood

# NEIGHBORHOOD_ROUTER
neighb_router = APIRouter(prefix='/neighborhood')


@neighb_router.post('/',
            response_description='get first neighborhood in the list',
            status_code=status.HTTP_200_OK,
            response_model=Neighborhood)
def read_one_neighborhood(
    request: Request,
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams()
    ):
    """
    TEST for getting one neighborhood
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_neighborhoods
    result = coll.find_one({})
    return {**result, 'id': IdMapper().toStr(result['_id'])}


@neighb_router.post('/list',
            response_description='get list of neighborhoods',
            status_code=status.HTTP_200_OK,
            response_model=list[Neighborhood])
def read_list_neighborhoods(
    request: Request,
    params: Annotated[HttpParams, Body(embed=True)] = HttpParams(nbr=5,page_nbr=1, filters={"value": "Bedford", "operator_field": OP_FIELD.CONTAIN, "field": "name"})
    ):
    """
    GET NEIGHBORHOODS LIST

    Args:
        params(HttpParams): required.
            nbr(int): number of items required.
            page_nbr(int): page number.
            filters(Filter): filters for request.
    Returns:
        list[Neighborhood]: the requested list with idObject as str.
    """
    coll: Collection = request.app.db_neighborhoods
    projection = {'_id':1,'geometry':1,'name':1}
    skip = (params.page_nbr - 1) * params.nbr
    query = Filter(**params.filters).make()
    if params.page_nbr>1:
        neighborhoods_cursor: list[dict] = coll.find(query, projection).skip(skip).limit(params.nbr)
    else:
        neighborhoods_cursor: list[dict] = coll.find(query, projection).limit(params.nbr)
    # id = idObject to str
    result = [{**neighb, 'id': IdMapper().toStr(neighb['_id'])} for neighb in neighborhoods_cursor]
    return result



@neighb_router.put('/update/',
                        response_description='update a neighborhood',
                        status_code=status.HTTP_200_OK,
                        response_model=Neighborhood)
def update_neighborhood(
    request: Request,
    id: Annotated[str, Body(embed=True)],
    changes: Annotated[dict, Body(embed=True)],
    params: Annotated[HttpParams, Body(embed=True)]
    ):
    """
    UPDATE A NEIGHBORHOOD

    Args:
        changes(dict): {id, changed_elements}.

    Returns:
        the updated neighborhood.
    """
    coll: Collection = request.app.db_neighborhoods
    result = coll.update_one({'_id': IdMapper().toObj(id)}, {"$set": changes})
    if result.matched_count==0:
        raise HTTPException(status_code=404, detail={"update": {"error": f"_id {id} not found"}})
    confirm = coll.find_one({'_id': IdMapper().toObj(id)})
    return confirm

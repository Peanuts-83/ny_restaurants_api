from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Body, status, Request, Response
from fastapi.encoders import jsonable_encoder
from pymongo.collection import Collection

from ..models.params import HttpParams
from ..models.utils import IdMapper
from ..models.models import Neighborhood

# NEIGHBORHOOD_ROUTER
neighb_router = APIRouter(prefix='/neighborhood')


@neighb_router.post('/',
            response_description='get first neighborhood in the list',
            status_code=status.HTTP_200_OK,
            response_model=Neighborhood)
def read_one_neighborhood(request: Request, params: Annotated[HttpParams, Body(embed=True)] = HttpParams(nbr=1)):
    """
    TEST for getting one neighborhood
    """
    # gain autocompletion by strongly typing collection
    coll: Collection = request.app.db_neighborhoods
    return coll.find_one({})


@neighb_router.post('/liste',
            response_description='get list of neighborhoods',
            status_code=status.HTTP_200_OK,
            response_model=list[Neighborhood])
def read_list_neighborhoods(request: Request, params: Annotated[HttpParams, Body(embed=True)] = HttpParams(nbr=5,page_nbr=1)):
    """
    GET NEIGHBORHOODS LIST

    Args:
        params(HttpParams): required.
            nbr(int): number of items required.
            page_nbr(int): page number.

    Returns:
        list[Neighborhood]: the requested list with idObject as str.
    """
    coll: Collection = request.app.db_neighborhoods
    skip = (params.page_nbr - 1) * params.nbr
    query = {}
    if params.page_nbr>1:
        neighborhoods_cursor: list[dict] = coll.find(query).skip(skip).limit(params.nbr)
    else:
        neighborhoods_cursor: list[dict] = coll.find(query).limit(params.nbr)
    # idObject to str
    result = [{**neighb, '_id': IdMapper().toStr(neighb['_id'])} for neighb in neighborhoods_cursor]
    return list(result)


@neighb_router.post('/create',
            response_description='create a neighborhood',
            status_code=status.HTTP_201_CREATED,
            response_model=Neighborhood)
def create_neighborhood(request: Request, neighborhood: Annotated[Neighborhood, Body(embed=True)]):
    """
    CREATE A NEIGHBORHOOD

    Args:
        neighborhood(Neighborhood): neighborhood data.

    Returns:
        created neighborhood.
    """
    coll: Collection = request.app.db_neighborhoods
    neighborhood = jsonable_encoder(neighborhood)
    try:
        new_neighborhood = coll.insert_one(neighborhood)
        created_neighborhood = coll.find_one(
            {"_id": new_neighborhood.inserted_id}
        )
        print(f'Success - Neighborhood #{new_neighborhood.inserted_id} CREATED')
        return created_neighborhood
    except Exception as e:
        print(f'Error on CREATE!', e)


@neighb_router.put('/update/',
                        response_description='update a neighborhood',
                        status_code=status.HTTP_200_OK,
                        response_model=Neighborhood)
def update_neighborhood(request: Request, changes: Annotated[dict, Body(embed=True)]):
    """
    UPDATE A NEIGHBORHOOD

    Args:
        changes(dict): {_id, changed_elements}.

    Returns:
        the updated neighborhood.
    """
    coll: Collection = request.app.db_neighborhoods
    _id = changes._id
    del changes['_id']
    result = coll.update_one({'_id': IdMapper().toObj(_id)}, {"$set": changes})
    if _id == None or result.modified_count==0:
        print(f'Error on UPDATE', changes)
        return {"update": {"error": f"_id {_id} not found"}}
    confirm = coll.find_one({'_id': IdMapper().toObj(_id)})
    return confirm



@neighb_router.delete('/delete',
                        response_description='delete a neighborhood',
                        status_code=status.HTTP_200_OK,
                        response_model=str)
def delete_neighborhood(request: Request, id: Annotated[str, Body(embed=True)]):
    """
    DELETE A NEIGHBORHOOD

    Args:
        id(str): id of neighborhood.

    Returns:
        the deleted neighborhood.
    """
    coll: Collection = request.app.db_neighborhoods
    # convert id if needed
    objectId = IdMapper().toObj(id)
    result = coll.delete_one({'_id': objectId})
    if result.deleted_count==1:
        print(f'Success - Neighborhood #{id} DELETED')
        return id
    else:
        print(f'Neighborhood #{id} not found!')
        return 'none'

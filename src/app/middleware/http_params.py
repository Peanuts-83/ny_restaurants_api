from enum import Enum
import json
from typing import Any, Optional, Tuple
from fastapi import HTTPException
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING

from ..models.utils import IdMapper

### OPERATOR ENUMS #
"""
https://www.mongodb.com/docs/manual/reference/operator/query/
$and: Joins query clauses with a logical AND returns all documents that match the conditions of both clauses.
$not: Inverts the effect of a query expression and returns documents that do not match the query expression.
$nor: Joins query clauses with a logical NOR returns all documents that fail to match both clauses.
$or: Joins query clauses with a logical OR returns all documents that match the conditions of either clause.

$regex: Selects documents where values match a specified regular expression.
$geoWithin: Selects geometries within a bounding GeoJSON geometry. The 2dsphere and 2d indexes support $geoWithin.
"""
class OP_FIELD(Enum):
    """
    Operators for single_filter
    """
    EQ = "$eq"
    NE = "$ne"
    CONTAIN = "$regex"
    IN = "$in"
    NOT_IN = "$nin"
    GT = "$gt"
    GTE = "$gte"
    LT = "$lt"
    LTE = "$lte"
    NOT = "$not"
    GEONEAR = "$geoNear"

class OP(Enum):
    """
    Operators for combined_filter
    """
    AND = "$and"
    OR = "$or"
    NOR = "$nor"

class SingleFilterType(BaseModel):
    value: Any
    operator_field: OP_FIELD
    field: str

class CombinedFilterType(BaseModel):
    filter_elements: list[SingleFilterType]
    operator: OP


class Filter():
    """
    Base filter for HttpParams.
    All params set to None by default.
    Some serve SingleFilter, others CombinedFilters.
    Contains main methods and error management applied for both filter classes.
    """
    value: Any = None
    operator_field: OP_FIELD = None
    field: str = None
    filter_elements: list[SingleFilterType] = None
    operator: OP = None

    def __init__(self, **args):
        super().__init__()
        for key, value in args.items():
            if key=='id':
                key='_id'
                value=IdMapper().toObj(value)
            setattr(self, key, value)

    def apply(self):
        raise NotImplementedError("Subclasses must implement apply() method")

    def make(self):
        l_request = {}
        if all(param is None for param in [self.value, self.operator, self.operator_field, self.operator_field, self.field, self.filter_elements]):
            return l_request
        if not self.filter_elements:
            # SingleFilter
            l_request = [{"$project": { "_id":0 }}]
            if not self.operator_field == OP_FIELD.GEONEAR.value:
                l_request.insert(0, {"$match": self.doBuildSingle(self.field, self.operator_field, self.value)})
            else:
                l_geoRequest = self.doBuildSingle(self.field, self.operator_field, self.value)
                l_request.insert(0, l_geoRequest)
        else:
            # CombinedFilter - geonear operator treated at last
            has_geoNearFilter = any(f['operator_field'] == OP_FIELD.GEONEAR.value for f in self.filter_elements)
            l_filters = [f for f in self.filter_elements if f['operator_field'] != OP_FIELD.GEONEAR.value]
            if has_geoNearFilter:
                l_geoNearFilter = [f for f in self.filter_elements if f['operator_field'] == OP_FIELD.GEONEAR.value][0]
                l_filters.append(l_geoNearFilter)
            elements: list[SingleFilter] = [ self.doBuildSingle(*list(single_filter.values())) for single_filter in l_filters ]
            l_request = self.doBuildCombined(elements, has_geoNearFilter)
        return l_request

    #  Requete en aggregation pipeline
    def doBuildSingle(self, field:str, operator:OP_FIELD, val:any) -> dict:
        # {<field>: {$eq: <value>}}
        if operator == OP_FIELD.EQ.value:
            return {field: {operator: val}}
        # {<field>: {$ne: <value>}}
        elif operator == OP_FIELD.NE.value:
            return {field: {operator: val}}
        # {<field>: {$not: <value{}>}} # value ex. {"$gt":5}
        elif operator == OP_FIELD.NOT.value:
            self.checkForDict(val).value # Dict required
            return {field: {operator: val}}
        # {<field>: {$regex: <value>}}
        elif operator == OP_FIELD.CONTAIN.value:
            return {field: {operator: f".*{val}.*", "$options": "i"}}
        # {<field>: {$in: <value[]>}}
        elif operator == OP_FIELD.IN.value or operator == OP_FIELD.NOT_IN.value:
            self.checkForList(val) # List required
            return {field: {operator: val}}
        # {<field>: {$lt|$lte|$gt|$gte: <value>}}
        elif operator in [OP_FIELD.GT.value, OP_FIELD.GTE.value, OP_FIELD.LT.value, OP_FIELD.LTE.value]:
            #  can operate on numbers and strings
            return {field: {operator: val}}
        # {<field>: near: {type: 'Point',coordinates: [ -73.982, 40.623 ] }, distanceField: 'distance', maxDistance: 500, query: {}, includeLocs: '0', spherical:}
        elif operator == OP_FIELD.GEONEAR.value:
            return {operator: {
                "near": {
                    "type": "Point", "coordinates": field
                },
                "distanceField": "distance",
                "maxDistance": val,
                "query": {},
                "spherical": True
            }}

    def doBuildCombined(self, elements: list, has_geoNearFilter = False) -> dict:
        """
        Hint: to get $all operator on values of sub-arrays, use $nor operator with reversed query.
        ex: {$nor: [{"grades.grade": {$gt: "A"}}]} > only grade $lte "A"
        ex: {"grades.grade": {$gt: "A"}} > some grade "A"
        """
        if not has_geoNearFilter:
            l_request = [{'$match': {}}, {"$project": { "_id":0 }}]
            # {$and|$or|$nor: <SingleFilter[]>}
            if self.operator in [OP.AND.value, OP.OR.value, OP.NOR.value] and len(elements) > 0:
                l_request[0]['$match'][self.operator] = elements
            elif len(elements) > 0:
                l_request[0]['$match'] = {*elements}
        else:
            l_request = [f for f in elements if OP_FIELD.GEONEAR.value in f]
            l_request.append({"$project": { "_id":0 }})
            l_query = [f for f in elements if OP_FIELD.GEONEAR.value not in f]
            if self.operator in [OP.AND.value, OP.OR.value, OP.NOR.value] and len(l_query) > 0:
                l_request[0][OP_FIELD.GEONEAR.value]['query']['$and'] = l_query
            elif len(l_query) > 0:
                l_request[0][OP_FIELD.GEONEAR.value]['query'] = {*l_query}
        return l_request

    # value ErrorManagement #
    # raise explicit error in response.body #
    def checkForList(self, value):
        if not isinstance(value, list):
            raise HTTPException(status_code=422, detail={"valueError": "Value should be an array.", "field": "value", "value": value})

    def checkForDict(self, value):
        if not isinstance(value, dict):
            raise HTTPException(status_code=422, detail={"valueError": "Value should be an object.", "field": "value", "value": value})

    def checkForNum(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            raise HTTPException(status_code=422, detail={"valueError": "Value should be a number.", "field": "value", "value": value})



class SingleFilter(Filter):
    """
    SINGLE_FILTER: { value, operator_field, field }
    params:
        field: Collection_field
        operator_field: OP_FIELD()
        value: Any
    """
    def __init__(self, value, operator_field: OP_FIELD, field: str): # type: ignore
        super().__init__()
        self.field = field
        self.operator_field = operator_field
        self.value = value

    def apply(self):
        for op in OP_FIELD:
            if self.operator_field == op.value:
                 return True
            else:
                return False



class CombinedFilter(Filter):
    """
    COMBINED_FILTER: { filter_elements: list[SingleFilter], operator}
        param:
            filter_elements: list of SingleFilter()
            operator: OP()
    """
    def __init__(self, filter_elements: list[SingleFilter]=None, operator: OP=None): # type: ignore
        super().__init__()
        self.filter_elements = filter_elements
        self.operator = operator

    def apply(self):
        for op in OP:
            if self.operator == op.value:
                return True
            else:
                return False

class SortWay(int,Enum):
    """
    Sort by order <ASC|DESC>.
    """
    ASC = 1
    DESC = -1

class SortParams(BaseModel):
    field: str
    way: int

# Error object returned in response.body #
class ValueError():
    ValueError: str
    field: str
    value: Any


### Request options #
class HttpParams(BaseModel):
    """
    Params applied for any request in need.
    """
    nbr: int = Field(default=None, ge=0)
    page_nbr: int = Field(default=None, ge=1)
    filters: dict = Field(default=None)
    sort: SortParams = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "nbr": 0,
                "page_nbr": 1,
                "filters": {},
                "sort": {"field":"name", "way":ASCENDING}  # Example sort value
            },
            "exclude_none": True  # Exclude fields with None value from schema
        }

### HttpParamsInterpreter #
def httpParamsInterpreter(params: HttpParams) -> list[int,int,Tuple[str,int]]:
    """
    Return skip and limit values.
    """
    skip = (params.page_nbr - 1) * params.nbr if params.page_nbr and params.nbr and (params.page_nbr - 1) * params.nbr > 0 else None
    limit = params.nbr if params.nbr and params.nbr > 0 else None
    sort = {params.sort.field: ASCENDING if params.sort.way==1 else DESCENDING} if params.sort and params.sort.field and params.sort.way else None
    return [skip, limit, sort]

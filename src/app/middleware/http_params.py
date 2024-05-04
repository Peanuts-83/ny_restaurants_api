from enum import Enum
from typing import Any, Optional
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

class OP(Enum):
    """
    Operators for combined_filter
    """
    AND = "$and"
    OR = "$or"
    NOR = "$nor"


class Filter():
    """
    Base filter for HttpParams.
    All params set to None by default.
    Some serve SingleFilter, others CombinedFilters.
    Contains main methods and error management applied for both filter classes.
    """
    value: Any = None
    operator_field: str = None
    operator_list: str = None
    field: str = None
    filter_elements: list = None
    operator: OP | OP_FIELD = None

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
        if all(param is None for param in [self.value, self.operator, self.operator_field, self.operator_list, self.field, self.filter_elements]):
            return l_request
        if not self.filter_elements:
            # SingleFilter
            l_request = self.doBuildSingle()
        else:
            # CombinedFilter
            elements = [ self.doBuildSingle(**single_filter) for single_filter in self.filter_elements ]
            l_request = self.doBuildCombined(elements)
        return l_request

    def doBuildSingle(self) -> dict:
        l_request = {}
        # {<field>: {$eq: <value>}}
        if self.operator_field == OP_FIELD.EQ.value:
            l_request[self.field] = self.value
        # {<field>: {$ne: <value>}}
        elif self.operator_field == OP_FIELD.NE.value:
            l_request[self.field] = {self.operator_field: self.value}
        # {<field>: {$not: <value{}>}}
        elif self.operator_field == OP_FIELD.NOT.value: # value ex. {"$gt":5}
            self.checkForDict(self.value).value # Dict required
            l_request[self.field] = {self.operator_field: self.value}
        # {<field>: {$regex: <value>}}
        elif self.operator_field == OP_FIELD.CONTAIN.value:
            l_request[self.field] = {self.operator_field: f".*{self.value}.*", "$options": "i"}
        # {<field>: {$in: <value[]>}}
        elif self.operator_field == OP_FIELD.IN.value or self.operator_field == OP_FIELD.NOT_IN.value:
            self.checkForList(self.value) # List required
            l_request[self.field] = {self.operator_field: self.value}
        # {<field>: {$lt|$lte|$gt|$gte: <value>}}
        elif self.operator_field in [OP_FIELD.GT.value, OP_FIELD.GTE.value, OP_FIELD.LT.value, OP_FIELD.LTE.value]:
            #  can operate on numbers and strings
            l_request[self.field] = {self.operator_field: self.value}
        return l_request

    def doBuildCombined(self, elements) -> dict:
        """
        Hint: to get $all operator on values of sub-arrays, use $nor operator with reversed query.
        ex: {$nor: [{"grades.grade": {$gt: "A"}}]} > only grade $lte "A"
        ex: {"grades.grade": {$gt: "A"}} > some grade "A"
        """
        l_request = {}
        # {$and|$or|$nor: <SingleFilter[]>}
        if self.operator in [OP.AND.value, OP.OR.value, OP.NOR.value]:
            l_request[self.operator] = elements
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
        value: Any
        operator_field: OP_FIELD()
        field: Collection_field
    """
    def __init__(self, value, operator_field: OP_FIELD, field: str): # type: ignore
        super().__init__()
        self.value = value
        self.operator_field = operator_field
        self.field = field

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


class Sort(int,Enum):
    """
    Sort by order <ASC|DESC>.
    """
    ASC = 1
    DESC = -1

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
    sort: Optional[tuple[str,Sort]] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "nbr": 0,
                "page_nbr": 1,
                "filters": {},
                "sort": ["name", ASCENDING]  # Example sort value
            },
            "exclude_none": True  # Exclude fields with None value from schema
        }

### HttpParamsInterpreter #
def httpParamsInterpreter(params: HttpParams) -> list[int]:
    """
    Return skip and limit values.
    """
    skip = (params.page_nbr - 1) * params.nbr if params.page_nbr else 0
    limit = params.nbr if params.nbr else 0
    sort = {"field":params.sort[0], "way":params.sort[1]} if not params.sort[0] is None and not params.sort[1] is None else None
    return [skip, limit, sort]

from enum import Enum
from bson import ObjectId

### ObjectId mapper #
class IdMapper():
    def toObj(self, id: str) -> ObjectId:
        """
        Set a str to ObjectId (bson) format for mongodb request.
        """
        return ObjectId(id) if not isinstance(id, ObjectId) else id

    def toStr(self, id: ObjectId) -> str:
        """
        Set ObjectId to str.
        """
        return str(id)
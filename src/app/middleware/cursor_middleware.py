from datetime import datetime
from pymongo import CursorType


def cursor_to_object(cursor: CursorType, rm_datetime: bool = False) -> dict|list:
    """
    Removes _id: ObjectId (not Json-interpretable) and convert additionnal problematic data.

    @param cursor:\n
        Cursor - Result of mongo query.

    @param rm_datetime <Optionnal>:\n
        bool - Convert datetime to string : datetime can cause Exceptions.

    """
    l_result = list(map(lambda item: {k:v for k,v in item.items() if k!='_id'}, list(cursor)))
    if rm_datetime:
        l_result = list(map(lambda item: convert_datetime_to_str(item), l_result))
    return l_result

def convert_datetime_to_str(obj):
    """
    Convert datetime to safe str.
    """
    if isinstance(obj, dict):
        return {k:convert_datetime_to_str(v) for k,v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_str(item) for item in obj]
    elif isinstance(obj, datetime):
        result = obj.strftime('%Y-%m-%d')
        return result
    else:
        return obj
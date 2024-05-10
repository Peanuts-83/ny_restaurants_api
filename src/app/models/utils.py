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


class MapUtils():
    def calculate_centroid(self, coord: list[list[float,float]]) -> list[float]:
        """
        Calculate geoCenter of a borough depending on it's polygon coordinates.

        @require list[list[float,float]]

        @return list[float,float]
        """
        if len(coord[0])!=2 or (not isinstance(coord[0][0],float) and not isinstance(coord[0][1], float)):
            if isinstance(coord[0],list):
                return self.calculate_centroid(coord[0])
        num_vertices = len(coord)
        sum_x = sum(point[0] for point in coord)
        sum_y = sum(point[1] for point in coord)
        centroid_x = sum_x / num_vertices
        centroid_y = sum_y / num_vertices
        return [centroid_x, centroid_y]

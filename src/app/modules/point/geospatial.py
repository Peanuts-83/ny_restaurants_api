from pymongo.collection import Collection

def doCreate2dSphere(coll: Collection, field: str):
    #  sparse: ignore empty coordinates
    return coll.create_index({field: "2dsphere"}, sparse = True)

def doGetNeighborhood():
    pass
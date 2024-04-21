from pymongo.collection import Collection

def doCreate2dSphere(coll: Collection, field: str):
    return coll.create_index({field: "2dsphere"})

def doGetNeighborhood():
    pass
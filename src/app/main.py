import logging
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware

from pymongo.collection import Collection

from .models.utils import MapUtils

from .middleware.http_middleware import CustomMiddleware
from .demo.demo_routes import router as demo_router
from .routes.router import router

logging.basicConfig(level=logging.INFO)
load_dotenv()
mongo_uri = os.getenv('MONGO_URI')

app = FastAPI()

# Define allowed origins, methods, and headers
origins = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:8080",
    "http://localhost:4200",
]

### Main Router #
app.include_router(demo_router)
app.include_router(router)

"""
MIDDLEWARES -
Can be used :
    * with @app.middleware('http') decorator on custom_middleware function.
    * with app.add(<class_custom_middleware(BaseHttpMiddleware)>, **options) by implementing dispatch method.
"""
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ErrorMiddleware handler
app.add_middleware(CustomMiddleware)

def init_2dsphere_index(coll: Collection, name:str, field:str):
    """
    Check for 2dsphere_index on collection, and creates it if missing.
    Usefull for geospatial queries.
    Target field contains:
        coordinates[long,lat]<float> - requiered
        type<Point|Polygon|...> - optional
    """
    index_info = coll.index_information()
    if f"2dsphere_{name}" not in index_info:
        index_name = f"2dsphere_{name}"
        coll.create_index(
            [(field, "2dsphere")], name=index_name, sparse=True
        )
        print(f"2dsphere_index created for {name} at field: {field}.")


@app.on_event('startup')
def startup_db_client():
    app.mongodb_client = MongoClient(mongo_uri)
    app.database = app.mongodb_client['sample_restaurants']
    app.db_restaurants = app.database['restaurants']
    init_2dsphere_index(coll=app.db_restaurants, name="restaurants", field="address.coord")
    logging.info(msg='2dSphere index processed for restaurants collection.')
    app.db_neighborhoods = app.database['neighborhoods']
    init_2dsphere_index(coll=app.db_neighborhoods, name="neighborhoods", field="geometry")
    logging.info(msg='2dSphere index processed for neighborhoods collection.')
    logging.info(msg='Successfully connected to mongodb_Atlas!')
    # For database managment, use console setup input:
    # console_setup()


@app.on_event('shutdown')
def shutdown_db_client():
    app.mongodb_client.close()

### Database collection updates #########################

def console_setup():
    user_input = input("### Choose any option:\n1. calculate all centroids\n2. unset centroids\n3. Exit\nYour choice?")
    if user_input.lower() == '1':
        print('### Centroid setup started on neighborhoods collection ###')
        set_centroid_field()
    elif user_input.lower() == '2':
        print('### Centroids will be removed on neighborhoods collection ###')
        unset_centroid_field()
    elif user_input.lower() == '3':
        print('### Centroid setup aborted.')
        return None

def set_centroid_field():
    """
    Set "geometry.centroid" field in neighnborhood's collection to define center's polygon coordinates.
    This setter method should be used only once at first use, or at any change in neighborhoods coordinates.
    """
    coll: Collection = app.db_neighborhoods
    for doc in coll.find():
        centroid = MapUtils().calculate_centroid(doc["geometry"]["coordinates"])
        coll.update_one(
            {"_id": doc["_id"]},
            {"$set": {"geometry.centroid": centroid}}
        )
        print(f'Name: {doc["name"]}, centroid: {centroid}')
    print('### Collection neighborhoods successfully updated ###')

def unset_centroid_field():
    """
    Unset "geometry.centroid" field in neighnborhood's collection.
    """
    coll: Collection = app.db_neighborhoods
    for doc in coll.find():
        coll.update_one(
            {"_id": doc["_id"]},
            {"$unset": {"geometry.centroid": ""}}
        )
        print(f'Name: {doc["name"]}, removed: OK')
    print('### Collection neighborhoods successfully updated ###')
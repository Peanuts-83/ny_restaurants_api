import logging
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware

from pymongo.collection import Collection

from app.middleware.http_middleware import CustomMiddleware
from app.demo.demo_routes import router as demo_router
from app.routes.router import router

logging.basicConfig(level=logging.INFO)
load_dotenv()
mongo_uri = os.getenv('MONGO_URI')

app = FastAPI()

### Main Router #
app.include_router(demo_router)
app.include_router(router)

"""
MIDDLEWARES -
Can be used :
    * with @app.middleware('http') decorator on custom_middleware function.
    * with app.add(<class_custom_middleware(BaseHttpMiddleware)>, **options) by implementing dispatch method.
"""
# CORS Middleware to handle CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
    app.db_neighborhoods = app.database['neighborhoods']
    init_2dsphere_index(coll=app.db_neighborhoods, name="neighborhoods", field="geometry")
    logging.info('Successfully connected to mongodb_Atlas!')

@app.on_event('shutdown')
def shutdown_db_client():
    app.mongodb_client.close()

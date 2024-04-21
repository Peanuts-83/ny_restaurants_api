import logging
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware

from .middleware.http_middleware import CustomMiddleware
from .demo.demo_routes import router as demo_router
from .routes.router import router

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

@app.on_event('startup')
def startup_db_client():
    app.mongodb_client = MongoClient(mongo_uri)
    app.database = app.mongodb_client['sample_restaurants']
    app.db_restaurants = app.database['restaurants']
    app.db_neighborhoods = app.database['neighborhoods']
    logging.info('Successfully connected to mongodb_Atlas!')

@app.on_event('shutdown')
def shutdown_db_client():
    app.mongodb_client.close()

import logging
from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import MongoClient

from demo.demo_routes import router as demo_router
from routes.routes import router

logging.basicConfig(level=logging.INFO)
config = dotenv_values('.env')

app = FastAPI()

### Main Router #
app.include_router(demo_router)
app.include_router(router)

@app.on_event('startup')
def startup_db_client():
    app.mongodb_client = MongoClient(config['MONGO_URI'])
    app.database = app.mongodb_client['sample_restaurants']
    app.db_restaurants = app.database['restaurants']
    app.db_neighborhoods = app.database['neighborhoods']
    logging.info('Successfully connected to mongodb_Atlas!')

@app.on_event('shutdown')
def shutdown_db_client():
    app.mongodb_client.close()

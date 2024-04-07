import logging
import os
from pymongo import MongoClient
from pymongo.collection import Collection


### DB #
def doInit():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client.sample_restaurants
    restaurants = db.get_collection('restaurants')
    neighborhoods = db.get_collection('neighborhoods')
    # Test connection at startup
    test = restaurants.find_one()
    logging.info('Connected successfully to Mongodb_Atlas')
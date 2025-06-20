"""MongoDB client utility."""
from pymongo import MongoClient
from config import settings

client = MongoClient(settings.MONGODB_URI)
db = client['myApp']
# Usage: db['collection_name']

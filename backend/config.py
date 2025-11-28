# backend/config.py
from pymongo import MongoClient

# Use local MongoDB for development. When deploying, replace this with your Atlas URI.
MONGO_URI = "mongodb://127.0.0.1:27017/"
DB_NAME = "smart_notice_agent"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

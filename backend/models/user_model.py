# backend/models/user_model.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from backend.config import db

users_collection = db["users"]

def create_user(name, email, password):
    """Create user and return inserted_id"""
    hashed_password = generate_password_hash(password)
    res = users_collection.insert_one({
        "name": name,
        "email": email,
        "password": hashed_password
    })
    return str(res.inserted_id)

def find_user_by_email(email):
    return users_collection.find_one({"email": email})

# kept for compatibility
def get_user_by_email(email):
    return find_user_by_email(email)

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

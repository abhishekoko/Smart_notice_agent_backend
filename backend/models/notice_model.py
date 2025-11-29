# backend/models/notice_model.py
from datetime import datetime
from bson import ObjectId
from config import db

notice_collection = db["notices"]  # MongoDB collection


def create_notice(data):
    """
    Insert a new notice into MongoDB.
    Ensures priority, deadline, and timestamps are stored properly.
    """
    notice = {
        "title": data["title"],
        "description": data["description"],

        # 🟥 NEW: AI Fields
        "priority": data.get("priority", "Low"),     # String (Critical/High/Medium/Low)
        "deadline": data.get("deadline"),            # ISO datetime string or None

        # User-based
        "user_id": data.get("user_id"),

        # Status fields
        "status": "pending",
        "completed": False,
        "completedDate": None,

        # Metadata
        "created_at": datetime.utcnow()
    }

    result = notice_collection.insert_one(notice)
    return str(result.inserted_id)


def get_all_notices(user_id=None):
    """
    Retrieve all notices (or only user-specific notices).
    """
    query = {}
    if user_id:
        query = {"$or": [{"user_id": user_id}, {"user_id": None}]}

    notices = list(notice_collection.find(query))

    for n in notices:
        n["_id"] = str(n["_id"])   # Convert ObjectId → String

    return notices


def delete_notice(notice_id):
    """Delete a notice by ID."""
    res = notice_collection.delete_one({"_id": ObjectId(notice_id)})
    return res.deleted_count > 0


def mark_notice_completed(notice_id):
    """Mark a notice as completed."""
    res = notice_collection.update_one(
        {"_id": ObjectId(notice_id)},
        {
            "$set": {
                "status": "completed",
                "completed": True,
                "completedDate": datetime.utcnow().strftime("%Y-%m-%d")
            }
        }
    )
    return res.modified_count > 0


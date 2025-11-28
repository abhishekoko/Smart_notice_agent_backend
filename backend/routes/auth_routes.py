# backend/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from backend.models.user_model import create_user, get_user_by_email, verify_password

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not all([name, email, password]):
            return jsonify({"error": "All fields required"}), 400

        if get_user_by_email(email):
            return jsonify({"error": "Email already exists"}), 400

        user_id = create_user(name, email, password)
        return jsonify({"message": "User created successfully", "id": str(user_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        user = get_user_by_email(email)
        if not user or not verify_password(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Send safe payload (no password)
        return jsonify({
            "message": "Login successful",
            "user": {
                "_id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email")
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

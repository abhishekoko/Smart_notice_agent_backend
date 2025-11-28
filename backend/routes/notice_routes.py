# backend/routes/notice_routes.py
import os
import uuid
from flask import Blueprint, request, jsonify

from backend.models.notice_model import (
    create_notice,
    get_all_notices,
    delete_notice,
    mark_notice_completed
)

from backend.utils.summarizer import TransformerSummarizer
from backend.services.priority_service import analyze_priority

notice_bp = Blueprint("notice_bp", __name__)
summarizer = TransformerSummarizer()


# ====================================================
# Create Notice (Manual)
# ====================================================
@notice_bp.route("/", methods=["POST"])
def create_notice_route():
    try:
        data = request.get_json()

        if not data or "title" not in data or "description" not in data:
            return jsonify({"error": "Missing title or description"}), 400

        # Step 1: Summarize
        if data.get("description"):
            data["description"] = summarizer.summarize(data["description"])

        # Step 2: Priority & Deadline
        ai_result = analyze_priority(data["description"])
        data["priority"] = ai_result["priority"]
        data["deadline"] = ai_result["deadline"]

        # Step 3: Save
        notice_id = create_notice(data)

        return jsonify({
            "message": "Notice created successfully",
            "id": str(notice_id),
            "priority": data["priority"],
            "deadline": data["deadline"]
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====================================================
# Get All Notices
# ====================================================
@notice_bp.route("/", methods=["GET"])
def get_notices():
    try:
        user_id = request.args.get("user_id")
        notices = get_all_notices(user_id)
        return jsonify(notices), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====================================================
# Delete Notice
# ====================================================
@notice_bp.route("/<notice_id>", methods=["DELETE"])
def delete_notice_route(notice_id):
    try:
        deleted = delete_notice(notice_id)
        if deleted:
            return jsonify({"message": "Notice deleted"}), 200
        return jsonify({"error": "Notice not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====================================================
# Mark Completed
# ====================================================
@notice_bp.route("/<notice_id>/complete", methods=["PUT"])
def complete_notice_route(notice_id):
    try:
        modified = mark_notice_completed(notice_id)
        if modified:
            return jsonify({"message": "Notice marked as completed"}), 200
        return jsonify({"error": "Notice not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====================================================
# Create Notice from OCR Image
# ====================================================
@notice_bp.route("/from-image", methods=["POST"])
def create_notice_from_image():
    try:
        # Validate image
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        image = request.files["image"]
        user_id = request.form.get("user_id")

        # Ensure uploads folder exists
        os.makedirs("uploads", exist_ok=True)

        # Save image with unique name
        filename = f"{uuid.uuid4().hex}_{image.filename}"
        save_path = os.path.join("uploads", filename)
        image.save(save_path)

        # Step 1 — OCR
        from backend.services.ocr_service import extract_text_from_image
        extracted_text = extract_text_from_image(save_path)

        # Check OCR success
        if not extracted_text or len(extracted_text.strip()) < 3:
            return jsonify({"error": "OCR could not read text"}), 400

        # Clean OCR text
        extracted_text = extracted_text.replace("—", "-").replace("|", "").strip()

        # Step 2 — Summarization
        summarized_text = summarizer.summarize(extracted_text)

        if not summarized_text or summarized_text.strip() == "":
            summarized_text = extracted_text

        # Step 3 — Priority & Deadline
        ai_result = analyze_priority(summarized_text)
        priority = ai_result["priority"]
        deadline = ai_result["deadline"]

        # Step 4 — Save Notice
        notice_data = {
            "title": "Image Notice",
            "description": summarized_text,
            "priority": priority,
            "deadline": deadline,
            "user_id": user_id,
            "source": "OCR"
        }

        notice_id = create_notice(notice_data)

        return jsonify({
            "message": "Notice created from image",
            "id": str(notice_id),
            "summary": summarized_text,
            "priority": priority,
            "deadline": deadline
        }), 201

    except Exception as e:     # ✔️ Correct indentation
        import traceback
        print("\n🔥🔥🔥 ERROR IN /from-image ENDPOINT 🔥🔥🔥")
        traceback.print_exc()
        print("--------------------------------------------------\n")
        return jsonify({"error": str(e)}), 500


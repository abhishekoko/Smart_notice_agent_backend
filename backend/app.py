# backend/app.py
from flask import Flask, send_from_directory
from flask_cors import CORS

from backend.routes.auth_routes import auth_bp
from backend.routes.notice_routes import notice_bp
from backend.config import db

import threading
from backend.services.email_listener import EmailReceiver
from backend.services.calendar_sync import run_calendar_sync   # ✅ NEW

from apscheduler.schedulers.background import BackgroundScheduler   # ✅ NEW


# ✅ Initialize Flask App
app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

# ✅ MongoDB connection
database = db

# ✅ Register API Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(notice_bp, url_prefix="/api/notices")


@app.route("/")
def serve_index():
    """Serve frontend (index.html)"""
    return send_from_directory("../frontend", "index.html")


# ✅ Background Email Listener
def start_email_listener():
    receiver = EmailReceiver()
    receiver.run()


if __name__ == "__main__":
    # ✅ Start IMAP email listener thread
    listener_thread = threading.Thread(target=start_email_listener, daemon=True)
    listener_thread.start()

    # ✅ Start Scheduler for Google Calendar Sync
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_calendar_sync, "interval", minutes=1)
    scheduler.start()

    print("🚀 Flask server started with:")
    print("   • 📬 Email Listener running in background")
    print("   • 🗓️ Google Calendar Auto-Sync every 1 minutes")

    app.run(debug=True, use_reloader=False)

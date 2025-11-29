# backend/app.py
from flask import Flask, send_from_directory
from flask_cors import CORS

from routes.auth_routes import auth_bp
from routes.notice_routes import notice_bp
from config import db

import threading
from services.email_listener import EmailReceiver
from services.calendar_sync import run_calendar_sync

from apscheduler.schedulers.background import BackgroundScheduler


# Initialize Flask App
app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

database = db

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(notice_bp, url_prefix="/api/notices")


@app.route("/")
def serve_index():
    return send_from_directory("../frontend", "index.html")


# Background Email Listener
def start_email_listener():
    receiver = EmailReceiver()
    receiver.run()


# Start background tasks immediately when file loads (works in Gunicorn)
listener_thread = threading.Thread(target=start_email_listener, daemon=True)
listener_thread.start()

scheduler = BackgroundScheduler()
scheduler.add_job(run_calendar_sync, "interval", minutes=1)
scheduler.start()


if __name__ == "__main__":
    app.run(debug=True)


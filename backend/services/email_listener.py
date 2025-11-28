# backend/services/email_listener.py
import imaplib
import email
import time
from datetime import datetime
from backend.config import db
from backend.utils.summarizer import TransformerSummarizer

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
IMAP_USER = "abhishek73197319@gmail.com"
IMAP_PASSWORD = "pqhw ozvy uxwd thme"
POLL_INTERVAL = 30  # seconds

notice_collection = db["notices"]
summarizer = TransformerSummarizer()

class EmailReceiver:
    def __init__(self, host=IMAP_HOST, port=IMAP_PORT, user=IMAP_USER, password=IMAP_PASSWORD, poll=POLL_INTERVAL):
        self.host = host
        self.port = port
        self.username = user
        self.password = password
        self.poll = poll

    def connect_imap(self):
        try:
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(self.username, self.password)
            print("✅ Connected to Gmail IMAP successfully.")
            return mail
        except imaplib.IMAP4.error as e:
            print(f"❌ IMAP login failed: {e}")
            return None

    def fetch_unseen_emails(self):
        mail = self.connect_imap()
        if not mail:
            return
        mail.select("inbox")
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            print("⚠️ Could not search inbox.")
            try:
                mail.logout()
            except:
                pass
            return

        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("subject", "(No Subject)")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and part.get_content_disposition() in (None, "inline"):
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode(errors="ignore")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")

            summarized_body = summarizer.summarize(body) if body else "(Empty Email)"
            notice_data = {
                "user_id": None,
                "title": subject,
                "description": summarized_body,
                "medium": "Email",
                "dueDate": datetime.utcnow().strftime("%Y-%m-%d"),
                "status": "pending",
                "createdDate": datetime.utcnow().strftime("%Y-%m-%d"),
            }
            notice_collection.insert_one(notice_data)
            print(f"📥 Saved new email as notice: {subject}")

        try:
            mail.logout()
        except:
            pass

    def run(self):
        print("📬 Email listener started.")
        try:
            while True:
                self.fetch_unseen_emails()
                time.sleep(self.poll)
        except KeyboardInterrupt:
            print("🛑 Email listener stopped.")

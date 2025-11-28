from pymongo import MongoClient
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime
import pickle
import os
import pytz
import dateparser
from dateparser.search import search_dates

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "smart_notice_agent"
COLLECTION_NAME = "notices"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

KEYWORDS = ["exam", "meeting", "holiday", "fee", "important", "result"]


def authenticate_google():
    creds = None
    if os.path.exists("token.pkl"):
        with open("token.pkl", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("backend/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.pkl", "wb") as token:
            pickle.dump(creds, token)
    return creds


def find_existing_event(service, mongo_id):
    """Check if event already exists by mongoId tag."""
    result = service.events().list(
        calendarId="primary",
        privateExtendedProperty=f"mongoId={mongo_id}",
        maxResults=1
    ).execute()
    events = result.get("items", [])
    return events[0] if events else None


def create_or_update_event(service, title, desc, date, mongo_id, time_str=None):
    """Create event with proper timezone-aware datetimes."""
    
    india = pytz.timezone("Asia/Kolkata")

    if time_str:
        # Parse event time safely
        try:
            event_time = datetime.datetime.strptime(time_str, "%I:%M %p").time()
        except:
            try:
                event_time = datetime.datetime.strptime(time_str, "%H:%M").time()
            except:
                event_time = datetime.time(9, 0)  # default 9 AM

        start_dt = india.localize(datetime.datetime.combine(date, event_time))
        end_dt = start_dt + datetime.timedelta(hours=1)

        body = {
            "summary": title,
            "description": desc,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "extendedProperties": {"private": {"mongoId": mongo_id}},
        }

    else:
        # All-day event
        body = {
            "summary": title,
            "description": desc,
            "start": {"date": date.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"date": (date + datetime.timedelta(days=1)).isoformat(), "timeZone": "Asia/Kolkata"},
            "extendedProperties": {"private": {"mongoId": mongo_id}},
        }

    # Update or create event
    existing = find_existing_event(service, mongo_id)
    if existing:
        service.events().update(calendarId="primary", eventId=existing["id"], body=body).execute()
    else:
        service.events().insert(calendarId="primary", body=body).execute()
        print(f"✅ Created event: {title}")


def run_calendar_sync():
    print("🗓️ Calendar Sync Running...")

    creds = authenticate_google()
    service = build("calendar", "v3", credentials=creds)

    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION_NAME]

    for notice in collection.find():
        title = (notice.get("title") or "").lower()
        desc = (notice.get("description") or "").lower()
        mongo_id = str(notice.get("_id"))
        fallback_due_date = notice.get("dueDate")

        if not fallback_due_date:
            continue

        # Extract date/time from text
        extracted = search_dates(desc, settings={"PREFER_DATES_FROM": "future"})
        parsed_date = None
        parsed_time = None

        if extracted:
            for _, dt in extracted:
                if dt.date() >= datetime.date.today():
                    parsed_date = dt.date()
                    if dt.time() != datetime.time(0, 0):
                        parsed_time = dt.strftime("%H:%M")
                    break

        # Fallback to dueDate from DB
        if parsed_date:
            date = parsed_date
        else:
            try:
                date = datetime.datetime.strptime(fallback_due_date, "%Y-%m-%d").date()
            except:
                continue

        time_str = notice.get("time") or notice.get("startTime") or parsed_time

        # Only sync important notices
        if any(k in title or k in desc for k in KEYWORDS):
            create_or_update_event(service, title.title(), desc, date, mongo_id, time_str)

    print("✅ Sync Done.")

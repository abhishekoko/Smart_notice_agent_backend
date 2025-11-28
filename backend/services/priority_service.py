import re
from datetime import datetime, timedelta
import pytz
from dateparser.search import search_dates

# Timezone
DEFAULT_TZ = "Asia/Kolkata"
TIMEZONE = pytz.timezone(DEFAULT_TZ)

# --- BASIC KEYWORDS ---
CRITICAL_KEYWORDS = {
    "immediate", "urgent", "asap", "final warning", "must submit", "last date",
    "no extension", "submit today", "deadline", "expires", "closing soon"
}

HIGH_KEYWORDS = {
    "important", "due soon", "submit soon", "respond", "follow up",
    "time sensitive", "required", "final notice"
}

# --- Simple tokenizer (no nltk needed) ---
def simple_tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9 ]+", " ", text)
    return text.split()


# --- Deadline extraction ---
def extract_deadline(text):
    if not text:
        return None

    now = datetime.now(TIMEZONE)
    t = text.lower()

    # Rule-based matches
    if "today" in t:
        return now
    if "tomorrow" in t:
        return now + timedelta(days=1)
    if "next week" in t:
        return now + timedelta(days=7)
    if "asap" in t or "soon" in t:
        return now + timedelta(days=2)

    # NLP based detection
    try:
        results = search_dates(
            text,
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now}
        )
        if results:
            dt = results[0][1]
            if not dt.tzinfo:
                dt = TIMEZONE.localize(dt)
            return dt
    except:
        return None

    return None


# --- Analyze priority ---
def get_priority_level(text, deadline=None):
    if not text:
        return "Unknown"

    tokens = simple_tokenize(text)
    token_text = " ".join(tokens)

    # Keyword detection
    if any(w in token_text for w in CRITICAL_KEYWORDS):
        priority = "Critical"
    elif any(w in token_text for w in HIGH_KEYWORDS):
        priority = "High"
    else:
        priority = "Low"

    if not deadline:
        return priority

    now = datetime.now(TIMEZONE)
    try:
        if not deadline.tzinfo:
            deadline = TIMEZONE.localize(deadline)
        left = deadline - now
    except:
        return priority

    # Adjust priority based on time
    if left.total_seconds() <= 0:
        return "CRITICAL (PASSED)"
    if left < timedelta(hours=24):
        return "Critical"
    if left < timedelta(days=3) and priority != "Critical":
        return "High"
    if left < timedelta(days=7) and priority not in ["Critical", "High"]:
        return "Medium"

    return priority


# --- MAIN FUNCTION ---
def analyze_priority(text, corpus=None):
    deadline = extract_deadline(text)
    priority = get_priority_level(text, deadline)

    return {
        "priority": priority,
        "deadline": deadline.isoformat() if deadline else None
    }

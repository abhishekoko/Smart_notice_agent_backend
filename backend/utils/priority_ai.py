import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from dateparser.search import search_dates
from datetime import datetime, timedelta
import pytz
import nltk

nltk.download('punkt')
nltk.download('stopwords')

# Timezone setup
DEFAULT_TZ = "Asia/Kolkata"
TIMEZONE = pytz.timezone(DEFAULT_TZ)

# Base keyword sets
CRITICAL_KEYWORDS = set([
    "immediate", "mandatory", "must submit", "final warning", "asap", "deadline",
    "no further extension", "submit today", "final call", "urgent submission",
    "time bound", "expires today", "closing soon", "last chance"
])

HIGH_KEYWORDS = set([
    "urgent", "final notice", "important", "required", "strictly enforced",
    "due soon", "kindly submit", "please respond", "follow up", "time sensitive",
    "response needed", "submission closing", "approaching deadline"
])

# --- AI keyword learning ---
def learn_new_keywords(text_corpus, n_clusters=3, top_n=10):
    if len(text_corpus) < 2:
        return {} 

    stop_words = set(stopwords.words('english'))
    clean_texts = []
    for text in text_corpus:
        tokens = word_tokenize(text.lower())
        tokens = [t for t in tokens if t.isalpha() and t not in stop_words]
        clean_texts.append(" ".join(tokens))

    vectorizer = TfidfVectorizer(max_df=0.9, min_df=1, ngram_range=(1, 2))
    X = vectorizer.fit_transform(clean_texts)
    if len(text_corpus) < n_clusters:
        n_clusters = len(text_corpus)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(X)
    feature_names = vectorizer.get_feature_names_out()
    clusters = {}
    for i in range(n_clusters):
        indices = kmeans.cluster_centers_[i].argsort()[-top_n:][::-1]
        clusters[i] = [feature_names[idx] for idx in indices]
    return clusters

def expand_keywords_with_ai(text_corpus):
    clusters = learn_new_keywords(text_corpus)
    new_critical = set()
    new_high = set()
    urgency_words = ["urgent", "deadline", "immediate", "submit", "due", "final", "required"]
    for _, words in clusters.items():
        if any(u in w for w in words for u in urgency_words):
            if "submit" in " ".join(words) or "immediate" in " ".join(words):
                new_critical.update(words)
            else:
                new_high.update(words)
    expanded_critical = CRITICAL_KEYWORDS.union(new_critical)
    expanded_high = HIGH_KEYWORDS.union(new_high)
    return expanded_critical, expanded_high

# --- Deadline detection ---
def extract_deadline(text):
    if not text:
        return None
    text = text.lower()
    now = datetime.now(TIMEZONE)
    if "asap" in text or "soon" in text:
        return now + timedelta(days=2)
    if "next week" in text:
        return now + timedelta(days=7)
    if "tomorrow" in text:
        return now + timedelta(days=1)
    if "today" in text:
        return now
    try:
        matches = search_dates(text, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': now})
        if matches:
            dt = matches[0][1]
            if not dt.tzinfo:
                dt = TIMEZONE.localize(dt)
            return dt
    except Exception:
        return None
    return None

# --- Priority logic ---
def get_priority_level(text, critical_words, high_words, deadline=None):
    if not text:
        return "Unknown"
    now = datetime.now(TIMEZONE)
    txt = text.lower()
    if any(word in txt for word in critical_words):
        priority = "Critical"
    elif any(word in txt for word in high_words):
        priority = "High"
    else:
        priority = "Low"
    if not deadline:
        return priority
    try:
        if not deadline.tzinfo:
            deadline = TIMEZONE.localize(deadline)
        delta = deadline - now
    except Exception:
        return priority
    if delta.total_seconds() <= 0:
        return "CRITICAL (PASSED)"
    if delta < timedelta(hours=24):
        return "Critical"
    if delta < timedelta(days=3) and priority != "Critical":
        priority = "High"
    elif delta < timedelta(days=7) and priority not in ["Critical", "High"]:
        priority = "Medium"
    return priority

# --- Main single-input function ---
def get_text_priority(user_text, corpus=None):
    # If no corpus provided, use base keywords
    if corpus and len(corpus) > 1:
        critical_words, high_words = expand_keywords_with_ai(corpus)
    else:
        critical_words, high_words = CRITICAL_KEYWORDS, HIGH_KEYWORDS

    deadline = extract_deadline(user_text)
    priority = get_priority_level(user_text, critical_words, high_words, deadline)
    return priority

# --- Interactive part ---
if __name__ == "__main__":
    user_input = input("Enter your task or message: ")
    result = get_text_priority(user_input)
    print(f"\n🟩 Priority Level: {result}")

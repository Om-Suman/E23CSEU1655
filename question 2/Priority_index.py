"""
Stage 6 - Priority Inbox
Fetches notifications from the API, scores them by type weight + recency,
and maintains a live top-N priority heap as new notifications stream in.
"""

import heapq
import time
import requests
from datetime import datetime, timezone
from dataclasses import dataclass, field
import os

# Load environment variables from .env when available (optional)
try:
    from dotenv import load_dotenv
    # Load .env located in the same folder as this script (question 2/.env)
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
except Exception:
    # dotenv is optional; fall back to existing environment variables
    pass
from typing import Optional

# ---------------------------------------------------------------------------
# Config (load from environment / .env)
# ---------------------------------------------------------------------------
# EXTERNAL_API_BASE_URL should be the base (e.g. http://4.224.186.213/evaluation-service)
base_url = os.getenv('EXTERNAL_API_BASE_URL', 'http://4.224.186.213/evaluation-service')
API_URL = f"{base_url.rstrip('/')}/notifications"
API_KEY = os.getenv('EXTERNAL_API_TOKEN', '')

TOP_N   = int(os.getenv('TOP_N', '10'))  # user-configurable; can be set in .env

# Type weights: higher = more important
TYPE_WEIGHT = {
    "placement": 3,
    "result":    2,
    "event":     1,
}
RECENCY_DECAY = 0.0001   # controls how fast score drops with age (seconds)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass(order=True)
class Notification:
    """
    Stored in a min-heap keyed by (negative priority_score, id).
    Negating the score turns Python's min-heap into an effective max-heap.
    """
    neg_score: float                                    # heap key  (lower = higher priority)
    id:        str         = field(compare=False)
    title:     str         = field(compare=False)
    body:      str         = field(compare=False)
    type:      str         = field(compare=False)
    is_read:   bool        = field(compare=False)
    created_at: str        = field(compare=False)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def compute_score(notif: dict) -> float:
    """
    score = type_weight  +  recency_bonus
    recency_bonus decays exponentially with age so newer notifications
    naturally float to the top when weights are equal.
    """
    ntype       = notif.get("notificationType", "event").lower()
    weight      = TYPE_WEIGHT.get(ntype, 1)

    created_str = notif.get("createdAt", "")
    try:
        created_dt  = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        age_seconds = (datetime.now(timezone.utc) - created_dt).total_seconds()
    except Exception:
        age_seconds = 9999

    recency = 1.0 / (1.0 + RECENCY_DECAY * age_seconds)   # 0 < recency ≤ 1
    return weight + recency


# ---------------------------------------------------------------------------
# Priority Inbox (max-heap via negated score)
# ---------------------------------------------------------------------------
class PriorityInbox:
    """
    Maintains the top-N unread notifications efficiently.

    Strategy:
      - Keep a min-heap of size ≤ N (keyed on neg_score).
      - For each incoming notification:
          • If heap size < N  → push unconditionally.
          • Else if new score > score of heap root (weakest in top-N) → replace root.
      - This gives O(log N) per insertion regardless of total notifications.
    """

    def __init__(self, n: int = TOP_N):
        self.n    = n
        self._heap: list[Notification] = []   # min-heap on neg_score

    def add(self, raw: dict) -> None:
        if raw.get("isRead", False):
            return                            # skip already-read notifications

        score = compute_score(raw)
        notif = Notification(
            neg_score  = -score,
            id         = str(raw.get("id", "")),
            title      = raw.get("title", ""),
            body       = raw.get("body", ""),
            type       = raw.get("notificationType", ""),
            is_read    = raw.get("isRead", False),
            created_at = raw.get("createdAt", ""),
        )

        if len(self._heap) < self.n:
            heapq.heappush(self._heap, notif)
        elif notif.neg_score < self._heap[0].neg_score:   # new score > weakest
            heapq.heapreplace(self._heap, notif)

    def top(self) -> list[Notification]:
        """Return top-N sorted highest-priority first."""
        return sorted(self._heap, key=lambda x: x.neg_score)  # ascending neg = descending score

    def __len__(self):
        return len(self._heap)


# ---------------------------------------------------------------------------
# API fetch
# ---------------------------------------------------------------------------
def fetch_notifications() -> list[dict]:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    resp = requests.get(API_URL, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # API may return {"notifications": [...]} or a bare list
    if isinstance(data, list):
        return data
    return data.get("notifications", data.get("data", []))


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
def display_top(inbox: PriorityInbox) -> None:
    top = inbox.top()
    print(f"\n{'='*60}")
    print(f"  TOP {inbox.n} PRIORITY NOTIFICATIONS  (showing {len(top)})")
    print(f"{'='*60}")
    for rank, n in enumerate(top, 1):
        score = -n.neg_score
        print(f"\n#{rank}  [{n.type.upper()}]  score={score:.4f}")
        print(f"   Title : {n.title}")
        print(f"   Body  : {n.body[:80]}{'...' if len(n.body)>80 else ''}")
        print(f"   Time  : {n.created_at}   ID: {n.id}")
    print(f"\n{'='*60}\n")


# ---------------------------------------------------------------------------
# Simulated live stream  (poll every POLL_INTERVAL seconds)
# ---------------------------------------------------------------------------
POLL_INTERVAL = 30   # seconds between refreshes

def run_live(n: int = TOP_N, poll_interval: int = POLL_INTERVAL) -> None:
    """
    Continuously polls the API and refreshes the priority inbox.
    In a real system this would be replaced by a WebSocket / Kafka consumer.
    """
    print(f"Starting Priority Inbox (top {n}, polling every {poll_interval}s) ...")
    while True:
        try:
            inbox = PriorityInbox(n=n)
            raw_notifications = fetch_notifications()
            print(f"Fetched {len(raw_notifications)} notifications from API.")
            for raw in raw_notifications:
                inbox.add(raw)
            display_top(inbox)
        except requests.HTTPError as e:
            print(f"[HTTP Error] {e}")
        except Exception as e:
            print(f"[Error] {e}")
        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# One-shot mode (for demo / screenshot)
# ---------------------------------------------------------------------------
def run_once(n: int = TOP_N) -> None:
    inbox = PriorityInbox(n=n)
    raw_notifications = fetch_notifications()
    print(f"Fetched {len(raw_notifications)} notifications.")
    for raw in raw_notifications:
        inbox.add(raw)
    display_top(inbox)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    n    = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_N

    if mode == "live":
        run_live(n=n)
    else:
        run_once(n=n)
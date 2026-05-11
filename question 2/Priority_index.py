import heapq
import time
import requests
from datetime import datetime, timezone
from dataclasses import dataclass, field
import os

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
except Exception:
    pass
from typing import Optional

base_url = os.getenv('EXTERNAL_API_BASE_URL', 'http://4.224.186.213/evaluation-service')
API_URL = f"{base_url.rstrip('/')}/notifications"
API_KEY = os.getenv('EXTERNAL_API_TOKEN', '')

TOP_N   = int(os.getenv('TOP_N', '10'))

TYPE_WEIGHT = {
    "placement": 3,
    "result":    2,
    "event":     1,
}
RECENCY_DECAY = 0.0001


class AuthenticationError(RuntimeError):
    pass


def _is_placeholder_token(token: str) -> bool:
    return token.strip() == "" or token.strip().upper() == "REPLACE_WITH_VALID_TOKEN"


def _require_api_key() -> str:
    if _is_placeholder_token(API_KEY):
        raise AuthenticationError(
            "EXTERNAL_API_TOKEN is missing or still set to REPLACE_WITH_VALID_TOKEN. "
            "Set a valid bearer token in question 2/.env or in the environment before running."
        )
    return API_KEY


def _pick(raw: dict, *keys: str, default=""):
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default


def normalize_notification(raw: dict) -> dict:
    message = _pick(raw, "body", "Message", default="")
    title = _pick(raw, "title", default=message)
    notification_type = _pick(raw, "notificationType", "Type", default="event")
    created_at = _pick(raw, "createdAt", "Timestamp", default="")

    return {
        "id": str(_pick(raw, "id", "ID", default="")),
        "title": str(title),
        "body": str(message),
        "notificationType": str(notification_type),
        "isRead": bool(_pick(raw, "isRead", "is_read", default=False)),
        "createdAt": str(created_at),
    }

@dataclass(order=True)
class Notification:
    neg_score: float
    id:        str         = field(compare=False)
    title:     str         = field(compare=False)
    body:      str         = field(compare=False)
    type:      str         = field(compare=False)
    is_read:   bool        = field(compare=False)
    created_at: str        = field(compare=False)

def compute_score(notif: dict) -> float:
    ntype       = str(notif.get("notificationType", "event")).lower()
    weight      = TYPE_WEIGHT.get(ntype, 1)

    created_str = notif.get("createdAt", "")
    try:
        created_dt  = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        age_seconds = (datetime.now(timezone.utc) - created_dt).total_seconds()
    except Exception:
        age_seconds = 9999

    recency = 1.0 / (1.0 + RECENCY_DECAY * age_seconds)
    return weight + recency

class PriorityInbox:
    def __init__(self, n: int = TOP_N):
        self.n    = n
        self._heap: list[Notification] = []

    def add(self, raw: dict) -> None:
        raw = normalize_notification(raw)
        if raw.get("isRead", False):
            return

        score = compute_score(raw)
        notif = Notification(
            neg_score  = -score,
            id         = str(raw.get("id", "")),
            title      = str(raw.get("title", "")),
            body       = str(raw.get("body", "")),
            type       = str(raw.get("notificationType", "")),
            is_read    = bool(raw.get("isRead", False)),
            created_at = str(raw.get("createdAt", "")),
        )

        if len(self._heap) < self.n:
            heapq.heappush(self._heap, notif)
        elif notif.neg_score < self._heap[0].neg_score:
            heapq.heapreplace(self._heap, notif)

    def top(self) -> list[Notification]:
        return sorted(self._heap, key=lambda x: x.neg_score)

    def __len__(self):
        return len(self._heap)


def fetch_notifications() -> list[dict]:
    token = _require_api_key()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
    resp = requests.get(API_URL, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    return data.get("notifications", data.get("data", []))


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


POLL_INTERVAL = 30

def run_live(n: int = TOP_N, poll_interval: int = POLL_INTERVAL) -> None:
    print(f"Starting Priority Inbox (top {n}, polling every {poll_interval}s) ...")
    while True:
        try:
            inbox = PriorityInbox(n=n)
            raw_notifications = fetch_notifications()
            print(f"Fetched {len(raw_notifications)} notifications from API.")
            for raw in raw_notifications:
                inbox.add(raw)
            display_top(inbox)
        except AuthenticationError as e:
            print(f"[Auth Error] {e}")
            return
        except requests.HTTPError as e:
            status_code = getattr(e.response, "status_code", "unknown")
            body = getattr(e.response, "text", "")
            if status_code == 401:
                print(
                    "[Auth Error] The external API rejected the token with 401 Unauthorized. "
                    "Check that EXTERNAL_API_TOKEN contains a valid bearer token."
                )
            else:
                print(f"[HTTP Error] {status_code}: {body or e}")
        except Exception as e:
            print(f"[Error] {e}")
        time.sleep(poll_interval)


def run_once(n: int = TOP_N) -> None:
    try:
        inbox = PriorityInbox(n=n)
        raw_notifications = fetch_notifications()
        print(f"Fetched {len(raw_notifications)} notifications.")
        for raw in raw_notifications:
            inbox.add(raw)
        display_top(inbox)
    except AuthenticationError as e:
        print(f"[Auth Error] {e}")
    except requests.HTTPError as e:
        status_code = getattr(e.response, "status_code", "unknown")
        body = getattr(e.response, "text", "")
        if status_code == 401:
            print(
                "[Auth Error] The external API rejected the token with 401 Unauthorized. "
                "Check that EXTERNAL_API_TOKEN contains a valid bearer token."
            )
        else:
            print(f"[HTTP Error] {status_code}: {body or e}")


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    n    = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_N

    if mode == "live":
        run_live(n=n)
    else:
        run_once(n=n)
# Notification System Design

---

## Stage 1

### Core Actions the Notification Platform Should Support

1. Fetch all notifications for the logged-in student
2. Fetch unread notifications only
3. Mark a notification as read (single / all)
4. Receive real-time push notifications

---

### REST API Endpoints

#### 1. Get All Notifications

```
GET /api/v1/notifications
```

**Headers**

```json
{
  "Authorization": "Bearer <jwt_token>",
  "Content-Type": "application/json"
}
```

**Response 200**

```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "notif_001",
        "title": "Placement Drive – Google",
        "body": "Google campus recruitment scheduled for 20 May.",
        "notificationType": "Placement",
        "isRead": false,
        "createdAt": "2026-05-10T09:00:00Z"
      }
    ],
    "total": 1,
    "unreadCount": 1
  }
}
```

---

#### 2. Get Unread Notifications

```
GET /api/v1/notifications?isRead=false
```

Headers: same as above.

**Response 200** — same shape as above, filtered to unread items only.

---

#### 3. Mark a Single Notification as Read

```
PATCH /api/v1/notifications/:id/read
```

**Headers**

```json
{
  "Authorization": "Bearer <jwt_token>"
}
```

**Response 200**

```json
{
  "success": true,
  "message": "Notification marked as read.",
  "data": { "id": "notif_001", "isRead": true }
}
```

---

#### 4. Mark All Notifications as Read

```
PATCH /api/v1/notifications/read-all
```

**Response 200**

```json
{
  "success": true,
  "message": "All notifications marked as read.",
  "data": { "updatedCount": 42 }
}
```

---

### JSON Schema — Notification Object

| Field            | Type    | Description                            |
| ---------------- | ------- | -------------------------------------- |
| id               | string  | Unique notification ID                 |
| title            | string  | Short headline                         |
| body             | string  | Full message                           |
| notificationType | enum    | `"Placement"` / `"Result"` / `"Event"` |
| isRead           | boolean | Has the student read it?               |
| createdAt        | string  | ISO-8601 UTC timestamp                 |

---

### Real-Time Notification Mechanism — WebSocket

```
WS /ws/notifications
```

**Handshake header**

```
Authorization: Bearer <jwt_token>
```

**Server → Client push event (JSON)**

```json
{
  "event": "NEW_NOTIFICATION",
  "data": {
    "id": "notif_099",
    "title": "Result Declared – Semester 6",
    "body": "Your Semester 6 result is now available.",
    "notificationType": "Result",
    "isRead": false,
    "createdAt": "2026-05-11T08:30:00Z"
  }
}
```

The server keeps one WebSocket connection per authenticated student. When any backend service publishes a new notification it emits the event over that socket, enabling instant delivery without polling.

---

## Stage 2

### Recommended Database — PostgreSQL

**Why PostgreSQL over MySQL / NoSQL?**

- ACID compliance is critical: a notification must either be fully saved or not saved at all — partial writes are unacceptable.
- PostgreSQL's native ENUM types map directly to `notificationType`.
- Mature support for partial indexes (`WHERE is_read = false`) which is the single most important optimisation for this workload.
- JSONB column available if metadata needs to be stored schemalessly in future.

---

### DB Schema

```sql
CREATE TYPE notification_type AS ENUM ('Event', 'Result', 'Placement');

CREATE TABLE notifications (
    id               UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id       BIGINT          NOT NULL,
    title            VARCHAR(255)    NOT NULL,
    body             TEXT            NOT NULL,
    notification_type notification_type NOT NULL,
    is_read          BOOLEAN         NOT NULL DEFAULT false,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Indexes (see Stage 3 for detailed rationale)
CREATE INDEX idx_notifications_student_unread
    ON notifications (student_id, created_at DESC)
    WHERE is_read = false;
```

---

### REST API Queries Based on Stage 1 Endpoints

```sql
-- GET /api/v1/notifications  (all for student)
SELECT * FROM notifications
WHERE student_id = $1
ORDER BY created_at DESC
LIMIT 50 OFFSET $2;

-- GET /api/v1/notifications?isRead=false
SELECT * FROM notifications
WHERE student_id = $1 AND is_read = false
ORDER BY created_at DESC;

-- PATCH /api/v1/notifications/:id/read
UPDATE notifications
SET is_read = true, updated_at = NOW()
WHERE id = $1 AND student_id = $2;

-- PATCH /api/v1/notifications/read-all
UPDATE notifications
SET is_read = true, updated_at = NOW()
WHERE student_id = $1 AND is_read = false;
```

---

### Problems as Data Volume Grows & Solutions

| Problem                                 | Solution                                                                         |
| --------------------------------------- | -------------------------------------------------------------------------------- |
| Full table scans on 5 M+ rows           | Composite partial index on `(student_id, created_at DESC) WHERE is_read = false` |
| Unread count queried on every page load | Cache unread count per student in Redis; invalidate on insert / mark-read        |
| Table bloat from old notifications      | Partition by month (`RANGE` on `created_at`) or archive rows older than 6 months |
| Write contention during bulk inserts    | Use async workers + a message queue (see Stage 5)                                |

---

## Stage 3

### Is the Original Query Accurate?

```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```

**Accuracy:** Yes, it is logically correct — it returns all unread notifications for student 1042 in reverse chronological order.

**Why it is slow:** With 5,000,000 rows and no index on `(studentID, isRead)`, the engine performs a **full table scan** on every request. At 50,000 students each triggering this query on page load the database is overwhelmed immediately.

---

### What to Change

1. **Add a composite partial index** — this is the single highest-impact change:

```sql
CREATE INDEX idx_notifications_student_unread
    ON notifications (student_id, created_at DESC)
    WHERE is_read = false;
```

- The `WHERE is_read = false` clause means the index only contains unread rows, keeping it small and fast.
- Once a notification is marked read it drops out of the index automatically.
- Estimated cost: O(log K) lookup where K = unread rows for that student (typically << 100), vs O(N) full scan where N = 5 M.

2. **Add a `LIMIT`** — never fetch unbounded rows:

```sql
SELECT id, title, body, notification_type, created_at
FROM notifications
WHERE student_id = 1042 AND is_read = false
ORDER BY created_at DESC
LIMIT 50;
```

3. **Select only needed columns** — avoid `SELECT *` to reduce I/O.

---

### Advice: "Add indexes on every column"

**This is bad advice.** Every index costs:

- Extra disk space (can be significant at 5 M rows).
- Write overhead — every INSERT / UPDATE / DELETE must also update all indexes.
- Planner confusion — too many indexes can make the query planner choose poorly.

Index only columns that appear in `WHERE`, `ORDER BY`, or `JOIN` conditions of real queries.

---

### Query — Placement Notifications in Last 7 Days

```sql
SELECT *
FROM notifications
WHERE notification_type = 'Placement'
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

Support this with:

```sql
CREATE INDEX idx_notifications_type_created
    ON notifications (notification_type, created_at DESC);
```

---

## Stage 4

### Problem

Notifications are fetched from the DB on **every page load** for every student. With 50,000 students this generates a constant flood of identical read queries that overwhelms the database.

---

### Proposed Solutions & Tradeoffs

#### Strategy 1 — Redis Cache (Recommended Primary Fix)

Cache the unread notification list per student with a short TTL.

```
Key:   notifications:unread:{student_id}
Value: JSON array of top-50 unread notifications
TTL:   60 seconds
```

**Flow:**

1. Page load → check Redis.
2. Cache HIT → return immediately (sub-millisecond, zero DB load).
3. Cache MISS → query DB, populate cache, return result.
4. On new notification insert or mark-read → `DEL notifications:unread:{student_id}` to invalidate.

**Tradeoffs:**

- Reduces DB load by ~95%+ for read-heavy workloads.
- Students may see notifications up to TTL seconds stale (acceptable given WebSocket real-time push already handles instant delivery).
- Adds operational complexity (Redis cluster, eviction policy).

---

#### Strategy 2 — Unread Count Cache Only

Store only the integer unread count in Redis; still hit DB for the actual list.

**Tradeoffs:**

- Much simpler than caching full payloads.
- Does not fix the DB query for the notification list itself.

---

#### Strategy 3 — HTTP Response Caching / ETags

Return `ETag` on the notification response. Client sends `If-None-Match`; server returns `304 Not Modified` if nothing changed.

**Tradeoffs:**

- Reduces bandwidth and serialisation cost.
- DB is still queried to compute the ETag.

---

#### Strategy 4 — WebSocket Push + Local State (Eliminates Polling)

Instead of fetching on every page load, load notifications once at login and update local state via WebSocket events. Page "refresh" reads local state, not DB.

**Tradeoffs:**

- Eliminates fetch-on-load entirely — best long-term solution.
- Requires frontend state management and reconnection handling.
- More complex to implement correctly.

---

**Recommended combination:** Redis cache (Strategy 1) + WebSocket push (Strategy 4). Cache handles the bulk of read traffic; WebSocket keeps state fresh without polling.

---

## Stage 5

### Shortcomings of the Original Implementation

```python
function notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        send_email(student_id, message)   # calls Email API
        save_to_db(student_id, message)   # DB insert
        push_to_app(student_id, message)  # real-time push
```

1. **Sequential processing** — 50,000 students processed one by one. Even at 10 ms per iteration that is 500 seconds (~8 minutes). Completely unacceptable.
2. **No fault isolation** — if `send_email` fails for student #200, the loop stops. Students 201–50,000 receive nothing.
3. **Atomicity coupling** — email sending and DB insert are not atomic. A crash between the two leaves the DB and email state inconsistent.
4. **No retry logic** — transient failures (network blip, Email API rate limit) are fatal.
5. **Tight coupling** — the HTTP request handler blocks until all 50,000 operations complete, causing request timeouts.

---

### What to Do When `send_email` Failed for 200 Students

With the current design: those 200 students silently never receive their email, and there is no record of the failure. The only recovery is a manual re-run — but which 200 students? Unknown.

---

### Should DB save and email send happen together?

**No — they should be decoupled.** The DB insert is the source of truth and must succeed first. Email is a side effect. Tying them together means a transient Email API failure rolls back the notification record, which is wrong.

---

### Redesigned Approach — Message Queue + Worker Pool

```text
                    ┌─────────────────────┐
HR clicks           │   notify_all()      │
"Notify All"  ───►  │  Enqueue 50k jobs   │
                    │  into message queue │
                    └──────────┬──────────┘
                               │  (returns immediately - non-blocking)
                    ┌──────────▼──────────┐
                    │   Message Queue     │  (e.g. RabbitMQ / Redis Streams)
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       Worker #1         Worker #2  ...   Worker #N
    (save_to_db          (same)           (same)
     send_email
     push_to_app)
```

---

### Revised Pseudocode

```python
# --- Publisher (called by HR action) ---
function notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        enqueue("notification_jobs", {
            "student_id": student_id,
            "message":    message,
            "enqueued_at": now()
        })
    # Returns instantly — no blocking

# --- Worker (runs in parallel, N instances) ---
function process_notification_job(job: dict):
    student_id = job["student_id"]
    message    = job["message"]

    # 1. Persist first — source of truth
    notification_id = save_to_db(student_id, message)
    if not notification_id:
        nack(job)          # requeue for retry
        return

    # 2. Send email with retry
    success = False
    for attempt in range(1, 4):             # up to 3 attempts
        if send_email(student_id, message):
            success = True
            break
        sleep(exponential_backoff(attempt))

    if not success:
        mark_email_failed(notification_id)  # flag in DB; schedule manual/batch retry
        log_error(student_id, "email_failed_after_retries")

    # 3. Push real-time (best-effort)
    push_to_app(student_id, notification_id)

    ack(job)   # remove from queue only after all steps complete
```

---

### Key Properties of the Redesign

| Property               | Mechanism                                                      |
| ---------------------- | -------------------------------------------------------------- |
| Non-blocking           | Publisher enqueues and returns; workers process asynchronously |
| Parallel               | N workers process jobs concurrently → 50k jobs in seconds      |
| Fault-isolated         | Worker failure affects only that job; queue retries it         |
| At-least-once delivery | Jobs re-queued on nack until acked after success               |
| Idempotency            | `notification_id` prevents duplicate DB rows on retry          |
| Observability          | Failed email IDs logged and flagged in DB for re-processing    |

---

## Stage 6

### Approach — Scoring Function + Min-Heap of Size N

**Priority Score Formula:**

```
score(notification) = type_weight + recency_bonus

type_weight:
    Placement → 3
    Result    → 2
    Event     → 1

recency_bonus = 1 / (1 + DECAY × age_in_seconds)
    where DECAY = 0.0001
    → ranges from ~1.0 (just arrived) to ~0.0 (very old)
```

This ensures a fresh Event can outrank a stale Placement notification, while a new Placement always beats everything else at equal recency.

---

### Maintaining Top N Efficiently as New Notifications Arrive

Use a **min-heap of size N** (keyed on score):

- If heap size < N → push the new notification unconditionally.
- If heap size == N and new score > heap root (weakest in current top-N) → `heapreplace` (pop root, push new).
- Otherwise discard.

**Cost:** O(log N) per incoming notification — constant with respect to total notification count. No need to re-sort all notifications.

**Invalidation:** When a notification is marked read, rebuild the heap from the API response (or maintain a secondary set for O(1) membership checks).

---

### Code

See `priority_inbox.py` in this repository.

**Usage:**

```bash
# One-shot — fetch and display top 10
python priority_inbox.py once 10

# Live polling mode — refreshes every 30 s
python priority_inbox.py live 10

# Custom N
python priority_inbox.py once 20
```

**Dependencies:**

```bash
pip install requests
```

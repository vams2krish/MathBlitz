# Database Design

## Schema

| Table | Purpose | Important Constraints |
| --- | --- | --- |
| `users` | Identity and password hash | Case-folded username is unique |
| `user_preferences` | Default activity, level, sound preference | One row per user; checked difficulty |
| `task_sessions` | Issued problem and protected solution | User-owned, timed task; indexed expiry |
| `attempts` | Immutable submitted outcomes | One attempt per task; checked result state |

`task_sessions` is intentionally separate from `attempts`: it prevents clients
from learning solutions before answering and provides a server-side deadline.
Score and leaderboard queries use `attempts` as their auditable event record.

## Indexes

- `users.canonical_username` supports sign-in lookup and uniqueness.
- `task_sessions(user_id, created_at)` supports learner task history.
- `task_sessions(expires_at)` supports cleanup of abandoned tasks.
- `attempts(user_id, submitted_at)` supports dashboard and recent activity.
- `attempts(activity_id, difficulty)` supports future curriculum analysis.

## Production Evolution

The local application creates schema tables through SQLAlchemy. The initial
PostgreSQL-compatible reference DDL is in `migrations/001_initial.sql`; a
production deployment should apply versioned migrations through its release
pipeline before new API instances receive traffic.

PostgreSQL is the intended shared production datastore. Redis does not replace
durable data: it stores only bounded caches and login-rate counters that can be
rebuilt or expire.

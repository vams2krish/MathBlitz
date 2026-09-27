# MathBlitz Architecture

## Goals

MathBlitz uses a thin web client and a stateless HTTP API. Learning rules do
not depend on FastAPI, SQLAlchemy, Redis, or browser state, which makes them
easy to test and allows new clients to use the same behavior.

## Boundaries

| Layer | Responsibility | Depends on |
| --- | --- | --- |
| `domain` | Difficulty policy, activity strategies, answer evaluation, scoring | Python standard library |
| `services` | Register/login, issue/submit task, preferences, dashboards | Domain and repositories/cache |
| `db` | SQLAlchemy models and query repositories | Relational database |
| `api` | Validation, authentication dependency, HTTP response contracts | Services |
| `frontend` | Accessible interaction and presentation | Versioned HTTP API |

This separation applies SOLID principles directly: generators implement one
strategy contract, services depend on repository/cache abstractions, and the
web transport does not own business rules.

## Request Flow

1. A learner signs in and receives a short-lived signed bearer token.
2. `POST /api/v1/tasks` asks an activity strategy for a problem and stores the
   answer in `task_sessions`; the response deliberately excludes that answer.
3. `POST /api/v1/tasks/{id}/submissions` validates ownership, prevents double
   submissions, checks the server deadline, calculates score, and writes an
   immutable attempt.
4. Dashboard and leaderboard reads aggregate attempts. Successful writes
   invalidate their cache entries.

## Scale And Reliability

- Run multiple stateless API processes behind a load balancer.
- Use PostgreSQL in production for transactions, indexing, backups, and read
  replicas; SQLite remains suitable for local development.
- Use Redis for shared login-rate counters and read-heavy summary caches. The
  memory implementation is intentionally only a local/test fallback.
- Expire unsubmitted `task_sessions` using a scheduled cleanup job in a
  hosted deployment.
- Serve `/assets` through a CDN and route `/api/v1` to API instances when
  traffic warrants separating frontend delivery.
- Emit structured request logs and metrics for authentication failures, task
  issue rate, submission latency, error rate, and cache hit ratio.

## Security

- Passwords use scrypt with a per-password random salt; legacy hashes are
  replaced after successful authentication.
- Task solutions never appear in task-issue responses.
- Tokens are HMAC signed and time limited. Production must set a secret key
  outside source control and should serve only over TLS.
- API validation constrains usernames, levels, answer formats, and leaderboard
  query sizes.

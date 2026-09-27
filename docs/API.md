# API Design

All endpoints are rooted at `/api/v1`. FastAPI also publishes an OpenAPI
document at `/openapi.json` and interactive docs at `/docs`.

## Resources

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | No | Database/cache readiness information |
| `POST` | `/auth/register` | No | Create an account and issue a token |
| `POST` | `/auth/login` | No | Sign in; Redis-backed failed-login throttle |
| `GET` | `/activities` | No | Daily-life category, icon/accent, variation estimate, and difficulty catalog |
| `POST` | `/tasks` | Bearer | Issue a timed task without returning its answer |
| `POST` | `/tasks/{task_id}/submissions` | Bearer | Record one answer and return feedback |
| `GET` | `/me/dashboard` | Bearer | Summary and recent attempts |
| `GET` | `/me/preferences` | Bearer | Read practice defaults |
| `PATCH` | `/me/preferences` | Bearer | Update practice defaults |
| `GET` | `/leaderboard?limit=10` | No | Ranked aggregate scores |

## Example Flow

```json
POST /api/v1/tasks
{
  "activity_id": "shopping-value",
  "difficulty": "Medium"
}
```

The response includes the prompt, hint, answer mode, and expiration. It does
not include a solution.

```json
POST /api/v1/tasks/{task_id}/submissions
{
  "answer": 36.00
}
```

The resulting attempt includes `result_status`, the correct answer, points,
and duration. A second submission for the same task returns `409 Conflict`.

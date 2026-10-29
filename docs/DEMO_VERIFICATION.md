# Live Demo Verification

**Date:** October 29, 2026

**Verdict:** local API and native Android demo verified; not a production release approval.

## Scope And Environment

The verified story is: a person signs in, chooses a daily-life scenario and
level, submits an answer, receives feedback, and sees durable progress through
the shared MathBlitz API. The native Android client was also used to navigate
the library, hints, rankings, and connection settings.

| Component | Environment used |
| --- | --- |
| Host | Windows, PowerShell |
| Python | 3.14.2 in the project virtual environment |
| FastAPI / Uvicorn | 0.136.3 / 0.47.0 |
| SQLAlchemy / HTTPX / pytest | 2.0.49 / 0.28.1 / 8.4.2 |
| API process | Uvicorn, loopback binding, no reload, non-default signing secret |
| Durable store | Isolated local SQLite databases; existing user data left untouched |
| Cache | In-memory adapter; Redis was not active |
| Android | Android 16 x86_64 emulator; debug app 2.0.1, version code 2 |
| Android manifest | Minimum SDK 23, target SDK 35 |
| Web UI | October 28 captures retained; October 29 browser access disabled in Work settings |

No public deployment URL was supplied or deployed. Docker's Linux engine was
not running. PostgreSQL, Redis-backed workers, hosted TLS, and production
traffic were not part of the verified environment.

## Automated Results

```text
24 passed in 12.16s
```

The complete suite includes the existing domain/security/API tests, four
leaderboard-limit regression cases, a JSON API-404 regression, and two new
live HTTP tests in `tests/test_live_http.py`.

The live tests start the actual Uvicorn process on a temporary local port,
with a temporary SQLite database and generated signing secret. They stop
their own process during teardown. They do not run against an existing user's
database or an external production service.

| Check | Observed result |
| --- | --- |
| Health and web assets | Health, HTML, JavaScript, CSS, and OpenAPI returned expected status/media types |
| Registration/login | New account `201`; duplicate `409`; wrong password `401`; case-insensitive login `200` |
| Public catalog | 12 categories and five canonical levels |
| Task matrix | All 60 category/level combinations issued and submitted successfully |
| Answer privacy | Issue responses omitted `correct_answer` and internal generation context |
| Duplicate answer | A later submission to an already-completed task returned `409` |
| Ownership | Another user's submission to the task returned `404` |
| Input contracts | Missing authentication `401`; unsupported level `422`; unknown category `404` |
| Concurrent duplicate | Eight competing requests: exactly one `201` and seven `409` responses |
| Durable state | Preferences and aggregate score survived a real server stop/start |
| Cache invalidation | Cached leaderboard limits 1, 5, 10, and 100 refreshed after a correct submission |
| API fallback | Unknown API paths returned a JSON `404`, not the web app's HTML |

The 60-case test reads expected answers from its private temporary database
as a submission oracle. It validates HTTP orchestration, scoring/persistence,
and response contracts. It is not an independent mathematical proof of every
generator, an enumeration of unique puzzles, or a load benchmark.

The existing suite additionally checks timeout recording, security headers,
password salting/verification, token tamper rejection, scoring tolerances,
and legacy difficulty translation.

## Native Live Walkthrough

The signed debug APK was installed and launched in a read-only emulator
session. A separate local showcase database was populated with synthetic
demo accounts and outcomes through the real registration/task/submission API.
Seeded scores and near-instant seeded response times are fixtures, not
evidence of human performance, learning improvement, or production latency.

| UI step | API/data evidence | Result |
| --- | --- | --- |
| Sign in | `POST /api/v1/auth/login` returned `200` | Native workspace opened |
| Load defaults | Catalog/preferences requests returned `200` | Budget Planner, Very Easy displayed |
| Issue scenario | `POST /api/v1/tasks` returned `201` | Prompt and countdown rendered |
| Let a task expire | A submission was recorded | Answer feedback and unchanged score displayed |
| Solve a fresh budget task | Correct answer submitted through native controls | Correct feedback, points, and progress displayed |
| Show hint | Existing server-provided hint displayed | Strategy text expanded without changing the outcome |
| Browse library | Catalog-backed category cards | Practical categories and descriptions visible |
| Open progress | Dashboard/leaderboard responses returned `200` | Account metrics and synthetic rankings visible |
| Open settings | Client connection screen | API URL and sign-out controls visible |
| Rotate device | Activity recreated and loaded saved account state | Wide level controls and scenario card rendered |

### Independent Budget Example

The on-screen question was:

> You have $279.00 for 14 days and want $5.00 left over. What is the most you can spend per day?

The independently calculated answer was `(279 - 5) / 14 = 19.5714...`, rounded
to `$19.57`. It was entered using the native Android UI, not a direct database
write or answer-reading endpoint.

The persisted attempt was inspected after the visible UI result:

```json
{
  "submitted_answer": 19.57,
  "correct_answer": 19.57,
  "result_status": "correct",
  "points": 14,
  "duration_ms": 66072
}
```

The native score changed from `279` to `293` and daily correct answers from
`9` to `10`. The score agrees with the implemented policy:
`10 + floor((90 - 66.072) / 5) = 14`.

No AndroidRuntime error entries appeared in the filtered application error
log snapshot after the walkthrough. This is a bounded observation, not a
guarantee of crash-free operation on other devices.

## Fixes Included In This Verification

1. Invalidate every supported leaderboard-limit cache key after a submission,
   rather than only the default top 10. The new regression reproduced stale
   results for limits 1, 5, and 100 before the fix.
2. Return JSON for unknown API routes. The regression reproduced an HTML
   response where an API client expected JSON.
3. Include repository flush as well as commit in the duplicate-submission
   integrity-error boundary, so a raced uniqueness failure can map to `409`.
4. Replace ambiguous overloaded Android layout helpers with an explicit
   weighted helper. Navigation, category text, task metadata, and action
   controls now receive real layout weights instead of zero-width margins.
5. Stack native task actions in portrait and retain horizontal actions in a
   wide layout; update both header and practice metrics after a submission.
6. Clear stale native task timers and ignore superseded task callbacks when
   navigating or generating another scenario.
7. Expose API URL setup before sign-in, clear authentication when changing
   servers, and reset the in-memory token on an unauthorized response.
8. Declare Android SDK/version metadata, retain the debug signing key across
   builds, and verify the build-cleanup target before recursive removal.

The settings screen was inspected, but changing to another live API host was
not part of this run. The pre-authentication URL and token-reset changes have
build/code-review coverage, not a full multi-host device test.

## Screenshot Evidence

All nine new Android images are actual emulator-window captures. No synthetic
mockups or altered scores were composited into them.

- [Welcome](images/android-welcome.jpg)
- [Workspace overview](images/android-overview.jpg)
- [Live practice](images/android-practice.jpg)
- [Correct answer and score](images/android-result.jpg)
- [Strategy hint](images/android-hint.jpg)
- [Scenario library](images/android-library.jpg)
- [Progress and leaderboard](images/android-progress.jpg)
- [Connection settings](images/android-settings.jpg)
- [Landscape layout](images/android-landscape.jpg)

The three original desktop images were captured during the October 28 browser
walkthrough. They were not relabeled as new October 29 browser-test evidence.

## Reproduce The Checks

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q tests/test_live_http.py -p no:cacheprovider
.\.venv\Scripts\python.exe -m compileall -q mathblitz tests app.py
node --check frontend\assets\app.js
.\android\build.ps1
```

Compilation and JavaScript syntax checks succeeded. Android compilation and
APK signature verification succeeded, with warnings about the Java 8 source
bootstrap path and deprecated Android APIs. A second build verified that the
debug-keystore file was unchanged.

To exercise the UI, start a local non-reload API process with a unique secret
and an isolated database, connect the emulator to `http://10.0.2.2:8000`, and
create a disposable test account. Do not put demo passwords, tokens, local
databases, or signing keys into Git. The showcased scores are fixtures, not
a required result for another run.

## Production Release Boundaries

- A fresh web UI walkthrough needs browser control enabled; do not treat the
  historical desktop captures as current responsive-browser coverage.
- Redis/PostgreSQL integration, multi-worker coherence, failover, migrations,
  backups/restores, and sustained-load behavior remain unverified.
- No hosted domain, HTTPS termination, external monitoring, or deployment
  rollback was tested.
- Swagger UI assets remain blocked by the current strict application CSP;
  `/openapi.json` is available, but interactive docs still need a scoped
  asset-hosting solution.
- Android coverage is one emulator in two orientations, not physical-phone,
  tablet, accessibility, or all-supported-version coverage.
- Native code is still concentrated in one activity. Protected release
  signing and app-store distribution are not implemented.
- Account lifecycle, child-audience safeguards, updated policies, and a
  complete scenario ambiguity/rounding/uniqueness audit remain release work.

The local demo is verified within this scope. A production-readiness claim
requires completing the outstanding checks, not just passing this suite.

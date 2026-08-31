# py-vocab

Extracts brand / tier-word / descriptor tokens from product titles using a local LLM, and builds up a confidence-scored vocabulary from repeated occurrences across titles.

## Why this exists

Product titles (mostly Ukrainian/mixed Ukrainian-English) get parsed into three categories:

- brand — manufacturer name
- tier — a specific marketed product line/variant name
- descriptor — color or material only

The LLM does the classification per title (see `src/llm/prompt.py` for the exact rules it's given). Everything downstream of that exists to make a single LLM call's output trustworthy at scale, since one extraction on one title is not reliable enough to build a vocabulary from directly.

## Core design decisions

**Why occurrence counts instead of trusting a single extraction.**
`Brand`, `TierWord`, `Descriptor`, and `BrandTier` all carry an `occurrence` column that increments every time that token (or brand+tier pair) shows up again across different titles. The idea is that noise from one bad extraction stays contained — it doesn't get treated as established vocabulary just because the LLM said so once. Nothing currently _acts_ on this count (e.g. gating brand_tier promotion behind a threshold) — right now it's just tracked. Using it to filter low-confidence pairs is a planned next step, not implemented yet.

**Why ProcessingAttempt exists separately from Title.**
Titles need to be reprocessable — a prompt change, a model swap, or a bug fix means re-running titles that were already processed once. Rather than overwrite a single result per title, every processing run creates a new `ProcessingAttempt` row, so a title accumulates a full history of attempts instead of losing the previous one.

**Why Title-Brand is many-to-many.**
Some titles genuinely reference more than one brand (co-branded products — e.g. a KRUPS machine built for Nescafé Dolce Gusto capsules). A single `brand_id` column on `Title` couldn't represent that, so brands attach via a `title_brands` junction table, same shape as `title_tier_words` / `title_descriptors`.

**Why there are three separate error/outcome tables (Thinking, AttemptError, HardError).**
Four outcomes are possible per attempt:

1. full success — `Thinking` row, no errors, status `succeeded`
2. partial success — LLM responded but the response failed validation — `Thinking` row (kept for debugging) + `AttemptError`, status `failed`
3. partial fail — the LLM call itself failed (timeout, bad connection) — no response to store, `AttemptError` only, status `failed`
4. complete fail — systemic (auth failure, service down) — not about any one title, so it's recorded once on the `Request` via `HardError`, not per-attempt, and the whole worker stops rather than continuing to fail the same way

`Thinking.response` holds the raw (unnormalized) LLM output; `Thinking.text` holds the model's reasoning trace, when the model/backend provides one (nullable — not every model returns this). Both exist specifically to make failures debuggable after the fact, not just to record success.

**Why the worker halts entirely on a systemic failure instead of skipping and retrying later.**
An auth failure or a dead LLM endpoint will fail identically on every subsequent title too — continuing would just burn through the whole batch reproducing the same error. On a systemic failure, any attempts not yet started are left alone (still `pending`, nothing to revert), the one that triggered it is marked `failed`, a single `HardError` is written on the `Request`, and the worker calls its own stop control (same mechanism as `POST /worker/stop`) so it waits for a human to actually fix the problem and restart it.

**Why processing is an in-process asyncio task, not a separate worker process.**
Simpler to deploy — one process instead of two — and SQLite doesn't support true concurrent writers anyway, so a separate process wouldn't buy real parallelism at the DB layer regardless. The tradeoff is that an API restart interrupts in-flight processing; attempts left at `running` from a crash need a manual reset (see `scripts/reset_attempts.py`) since there's no automatic stale-attempt recovery yet.

**Why titles within a request are processed concurrently, capped by a semaphore.**
`LLM_CONCURENT_REQ` in `.env` controls how many LLM calls run at once. Titles are loaded 200 at a time (one full `Request`, see chunking below) but only N run against the LLM concurrently — bounded by local LLM server throughput, not arbitrary.

**Why title submissions are chunked into separate `Request` rows of max 200 titles.**
Keeps each `Request`/batch a manageable, boundable unit — the worker always processes one `Request` fully (oldest first) before moving to the next, so `Request.titles_amount` stays a meaningful progress denominator instead of an unbounded number.

**Why SQLite, and what that constrains.**
Local dev choice. SQLite allows only one writer at a time regardless of app-level concurrency — WAL mode (enabled via a PRAGMA listener in `Database.__init__`) lets readers and a writer coexist without blocking, but writes still serialize underneath. This is fine at current scale (a DB write is milliseconds against an LLM call that takes seconds) but is a real constraint if this ever needs to scale past single-machine local processing — moving to Postgres/MySQL would remove it, and the code is written against plain SQLAlchemy 2.0 (`select()`/`AsyncSession`, no SQLite-specific query syntax) specifically so that swap wouldn't require rewriting the query layer, just the DSN and driver.

**Why a request's derived `failed` status means it has a `HardError`, not that some title inside it failed.**
A `Request` can be full of a mix of succeeded and failed titles and still count as `succeeded` overall, since per-title failures are normal and expected at scale. Only a systemic failure, the kind that halts the whole worker, marks the batch itself as failed.

**Why a title's status within `GET /requests/{id}` is a single value, not a "most recent attempt" lookup.**
Reprocessing a title creates a new `Request` with a new attempt, it never adds a second attempt to the same request. So a title can never have more than one attempt within a given request, and the query relies on that being structurally guaranteed rather than picking a "latest" one.

## Not yet wired up

- No confidence threshold is enforced anywhere — `occurrence` is tracked but nothing currently reads it to decide whether a brand/tier pairing is "trustworthy."
- No automatic recovery for attempts stuck at `running` after a crash/restart.
- A desktop app is planned to manage processing (rerun failed titles, rerun specific ones) against the API — not built yet.
- Titles in `GET /requests/{id}` currently only report counts, `brand_count`, `tier_word_count`, `descriptor_count`, not the actual brand/tier/descriptor names, still just numbers standing in for the real review data.

## Running it

uv sync
uv run alembic upgrade head
uv run main.py

Requires a `.env` (see `.env.example` for the full set of variables). The LLM is expected to be OpenAI-compatible (developed against a local LM Studio server) and support `response_format: json_schema`.

Worker processing is off by default — call `POST /worker/start` to begin, even after submitting titles.

## API

- `GET /health` — liveness check
- `POST /requests` — submit a list of titles for processing; chunks into `Request`s of up to 200 and creates a `ProcessingAttempt` per new (deduplicated) title
- `POST /worker/start` / `POST /worker/stop` — control background processing
- `GET /worker/status` — whether the worker is running and currently mid-batch
- `GET /requests` — list requests, paginated, filterable by derived status (pending/running/succeeded/failed), sortable by created_at, hard_error_count, or attempt_error_count
- `GET /requests/{id}` — one request's detail plus its titles, paginated and filterable by attempt status, sortable by title, brand_count, tier_word_count, descriptor_count, total_word_count, attempt_error_count, status, or total_tokens

## Schema layout

Models live in `src/db/models.py`. CRUD is one file per model under `src/db/crud/`, kept to plain data access — no business logic. Orchestration (what happens across multiple models/tables in one operation) lives in `src/service/`. `src/worker/` is just the polling loop and its start/stop state; the actual per-title processing logic lives in `src/service/title.py` and `src/service/llm.py`.

Migrations are managed with Alembic (`alembic/`) — SQLite requires batch mode for most `ALTER`-style changes, already configured in `alembic/env.py` (`render_as_batch=True`).

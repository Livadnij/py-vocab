# py-vocab

Extracts brand, tier and descriptor tokens from product titles using a local LLM, and builds a vocabulary from the results. Every attempt, prompt, reasoning trace and error is stored so extraction quality can be reviewed and compared across prompts.

## Why it exists

py-vocab is the Python rebuild of an earlier TypeScript vocabulary builder, which itself came out of Fuzcompare, a deterministic fuzzy product matcher.

> The idea of Fuzcompare came to me when I was scraping stuff for a client. I wondered how I can compare prices of two identical products if I don't have any shared value between them. For example, one website can have a barcode displayed on the page, or it can come in the network response. Basically, I can get it one way or another, but the product on another website that looks identical to me has no barcode, and the only information I can rely on is the name of the product. When I look at both of them, I can clearly see that they are identical, and I don't need any shared information like identical codes. I tried analyzing how a human can do that and came up with the idea that we rely on the set of available data, like images showing the same product, product titles mentioning the same brand, tier, color, etc. So I became obsessed with recreating something that allows a machine, code that is completely deterministic, to perform something complex that is usual for a human being.

> While building that project, I encountered some limitations and problems. For example, code can't understand what each word means and can't distinguish an item from an addition for the same item. In the title they still have the same product name, but the meaning is completely different, and this difference lies in the small words which can't be used in comparison. So I came up with another idea, giving weight to each word. Based on weight, I can drop words that are useless for comparison and rate important words accordingly. The first prototype worked with only JavaScript arrays filled with small amounts of data and was unable to cover all needs, so the most logical thing was to make the arrays larger. That's when the vocab generator project was born.

> At first it was written in TypeScript and Node, and it was already splitting titles into separate words and dividing them into groups using an LLM. However, because it was processing titles in batches, it was very unreliable. Some words were mangled, some obvious ones were just dropped, and because of batches I couldn't troubleshoot each of them separately or cleanly validate what went wrong. So time passed, and when I began learning Python, I remembered the vocab generator project and thought I could recreate it better this time. So I began with an SQLite database, made the first DB structure and changed it countless times while perfecting py-vocab. This time I'm not processing titles in batches but one title at a time, concurrently.

That last point explains most of the design below. Every title is its own attempt and everything the model returned is stored, so a bad extraction can be traced and retried on its own.

I plan to recreate Fuzcompare inside py-vocab behind the same API. When the matcher meets a brand or tier it cannot compare, it would call py-vocab, process the titles, update the vocabulary and run the comparison again.

## What it does

Product titles (mostly Ukrainian or mixed Ukrainian-English) are submitted through the API. Each new title gets a `ProcessingAttempt`. A worker sends pending attempts to an OpenAI-compatible LLM and parses the JSON response into tokens of three kinds.

- brand is the manufacturer name
- tier is a specific marketed product line or variant name
- descriptor is a color or material only

The seed prompt lives in the `783d13962185` migration. At runtime the worker always uses whichever prompt is marked default in the `prompts` table.

## Current state

Working today

- Title submission with deduplication, listing with search, sorting and pagination, and a detail view with extracted words and attempt history.
- Background worker that processes pending attempts concurrently, capped by `LLM_CONCURENT_REQ`.
- Prompt management in the database. Prompts can be created, listed with usage counts, and set as default. Every `Thinking` row records which prompt produced it.
- Per-title retry by creating a new attempt, with the full attempt history kept. A title that already has a pending or running attempt does not get a second one.
- Attempt detail view with the raw response, reasoning trace when the model provides one, token counts, duration, prompt text and errors.
- Systemic failure handling. An authentication or permission error, a missing model or an unreachable model server halts the run, marks the triggering attempt failed and writes a `HardError`. Timeouts count as per-title failures.
- Automatic recovery. Attempts left at `running` go back to `pending` and their partial `Thinking` and error rows are deleted, both on startup after a crash and when the worker is stopped with `POST /worker/stop`.
- Normalized vocabulary. Every stored word goes through one shared normalization, so spelling and case variants of the same word end up as a single row.
- Live worker status over server-sent events.

Not built yet

- Nothing uses occurrence counts to filter or trust vocabulary. They are only reported.
- No tier-to-brand pairing is stored. Brands, tier words and descriptors attach to titles independently.
- No authentication on the API.
- There are no endpoints to browse brands, tier words or descriptors on their own.

## Design decisions

**One attempt row per processing run.** Titles must be reprocessable after a prompt change, model swap or bug fix. Each run creates a new `ProcessingAttempt`, so a title keeps its full history instead of losing the previous result.

**Words attach to titles through junction tables.** `title_brands`, `title_tier_words` and `title_descriptors` are many-to-many because a title can legitimately name more than one brand, for example a KRUPS machine built for Nescafé Dolce Gusto capsules. When a title is reprocessed successfully, its links are replaced with the new result.

**Occurrence is derived, not stored.** The number of titles a word appears in is counted from the junction tables when a title detail is requested. That keeps it correct without extra bookkeeping, and it is the basis for judging how trustworthy a word is.

**Four outcomes are recorded separately.**

1. Full success has a `Thinking` row, no errors, and status `succeeded`.
2. Partial success means the LLM answered but the response failed parsing, validation or normalization. The `Thinking` row is kept for debugging, an `AttemptError` is added, and status is `failed`.
3. Partial failure means the LLM call itself failed, for example a timeout or bad connection. There is no response to store, so only an `AttemptError` is written and status is `failed`.
4. Complete failure is systemic, such as an auth failure, an unreachable or misconfigured model server, or a missing default prompt. It is not about any one title, so it is recorded once as a `HardError`.

`Thinking.response` holds the raw LLM output. `Thinking.text` holds the reasoning trace and is nullable because not every backend returns one.

**Hallucinated tokens are dropped.** After parsing, any token that does not appear in the title is removed and logged as an `AttemptError`. The comparison is word level and ignores case and punctuation, so a model answer of `tplink` matches a title that says `TP-Link`. If nothing survives, the attempt fails.

**Words are stored in one normalized form.** A token that passes validation is stored normalized, which means Unicode compatibility normalization, lowercase, and every character that is not a letter or digit removed. `TP-Link`, `tp-link` and `TPLink` all become `tplink`, and Cyrillic letters are kept as they are. The rule lives in `src/utils/normalize.py` with no dependencies on the rest of the app, so the same function can be reused for lookups when the matcher is built into this project. The cost is that stored words lose their original punctuation, for example `kruger&matz` is stored as `krugermatz`.

**The worker halts on systemic failure.** An authentication failure, a missing model or a dead model server fails identically for every remaining title, so continuing would only burn through the batch. Attempts not yet started stay `pending`. Attempts already in flight when the failure hits also fail, since they were using the same server.

**Processing is an in-process asyncio task.** One process is simpler to deploy, and SQLite allows a single writer anyway, so a separate worker would not add real parallelism at the database layer. An API restart or a manual stop interrupts in-flight work, and the interrupted attempts are returned to `pending` automatically.

**SQLite with WAL.** WAL lets readers and the writer coexist, but writes still serialize. This is fine at current scale because a write takes milliseconds against an LLM call that takes seconds. The code uses plain SQLAlchemy 2.0 with `select()` and `AsyncSession`, so moving to Postgres should only need a new DSN and driver.

**Attempt detail responses are cached when final.** `GET /attempts/{id}` returns an immutable cache header once the attempt is `succeeded` or `failed`.

## Running it

Copy `.env.example` to `.env` first. The variables are

- `LLM_BASE_URL` and `LLM_API_KEY` for the OpenAI-compatible endpoint
- `LLM_MODEL` for the model name
- `LLM_CONCURENT_REQ` for the number of simultaneous LLM calls (the spelling is intentional and matches the code)
- `PRODUCTION` to hide the docs endpoints and lower log verbosity
- `DSN` for the database, SQLite by default

```
uv sync
uv run alembic upgrade head
uv run main.py
```

The LLM must support `response_format` with `json_schema`. Development used a local LM Studio server with `google/gemma-4-e4b`.

The worker does not start on its own. Submit titles, then call `POST /api/v1/worker/process`. Interactive docs are at `/docs` when `PRODUCTION` is false.

## API

All routes are under `/api/v1`.

General

- `GET /health` is a liveness check.

Worker

- `POST /worker/process` starts processing pending attempts. The body takes an optional `limit`. It returns 409 if the worker is already running.
- `POST /worker/stop` cancels the running task and returns its in-flight attempts to `pending`.
- `GET /worker/status` returns whether the worker is processing.
- `GET /worker/events` is a server-sent event stream of worker status changes.

Titles

- `POST /titles` accepts a list of titles, deduplicates them, and creates a pending attempt for each new one. Returns all matching titles.
- `GET /titles` lists titles with the counts of brands, tier words and descriptors. It supports `q` search, `limit`, `offset`, `order`, and `sort` by `id`, `title`, `created_at`, `attempt_count`, `brand_count`, `tier_word_count`, `descriptor_count` or `total_word_count`.
- `GET /titles/{id}` returns the title with its words and their occurrence counts, plus its attempt history.
- `POST /titles/{id}/attempts` creates a new pending attempt for reprocessing. If the title already has a pending or running attempt, that attempt is returned instead.

Attempts

- `GET /attempts/{id}` returns status, thinking data, the prompt used, and errors.

Prompts

- `POST /prompts` creates a prompt.
- `GET /prompts` lists prompts with `titles_used_count`, sortable by `id`, `created_at` or `titles_used_count`.
- `POST /prompts/{id}/set-default` makes a prompt the one the worker uses. Only one prompt can be default, enforced by a partial unique index.

Hard errors

- `GET /hard-errors` lists systemic failures, paginated.

## Code layout

- `main.py` wires the app, runs startup recovery and holds shared state (database, LLM client, worker state).
- `src/api/` holds thin route handlers.
- `src/service/` holds orchestration across tables. `processing.py` is the per-attempt pipeline and `llm.py` handles LLM calls and token validation.
- `src/db/models.py` holds the models
- `src/db/crud/` holds plain data access with one file per area and no business logic.
- `src/llm/` holds the OpenAI client wrapper and response parsing.
- `src/utils/` holds pure helpers with no project dependencies. `normalize.py` is the word normalization rule.
- `src/worker/` holds the processing entry point and the worker state with its event subscribers.
- `src/schemas/` holds the Pydantic request and response models.
- `alembic/` holds migrations. SQLite needs batch mode for most `ALTER` changes, which is enabled in `alembic/env.py` with `render_as_batch=True`.

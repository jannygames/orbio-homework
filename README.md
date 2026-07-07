# Mini AI Product Assistant

A small AI chat assistant that answers questions about products and knows how to use
tools (tool calling), backed by Google Gemini, FastAPI, and PostgreSQL, with a
React + Tailwind chat UI. The assistant's replies are streamed to the UI token-by-token
over Server-Sent Events.

## Quick start

```bash
cp .env.example .env
# then edit .env and set GEMINI_API_KEY (get one at https://aistudio.google.com/apikey)

docker compose up --build
```

- Chat UI: http://localhost:3000
- API + interactive Swagger docs: http://localhost:8000/docs
- Raw OpenAPI schema: http://localhost:8000/openapi.json

That's it — `docker compose up` starts the database, backend and frontend together.
Tables are created automatically on backend startup.

## Architecture

```
orbio-homework/
  products.json          # static product catalog, read by the product tools
  docker-compose.yml
  backend/                # FastAPI app
    app/
      main.py             # app factory, lifespan (DB table creation, LLM client init), CORS, error handlers
      core/config.py      # Pydantic Settings (env-driven config)
      db/                 # SQLAlchemy async engine/session + ORM models
      schemas/            # Pydantic request/response models
      repositories/       # data-access layer (Conversation/Message)
      services/
        product_tools.py  # tool registry + implementations (search, details, compare, categories, recommend)
        llm_service.py    # Gemini turn loop: history -> LLM -> tool calls -> persistence -> stream
      api/
        deps.py           # DB session / LLM client dependency injection
        routes/            # chat + health endpoints
    tests/                # pytest suite (fast, no real network/DB dependency)
  frontend/               # React + Vite + TypeScript + Tailwind chat UI
    src/
      hooks/useChat.ts    # streaming/abort/reset state machine (SSE consumer)
      components/         # presentational pieces (Composer, MessageList, Markdown, ...)
      lib/format.ts       # tool-payload summaries for the inline tool activity rows
```

### Data model

Two tables, both created automatically on startup:

- **`conversations`** — just an id + timestamp. The "current" conversation is always
  the most recently created row; a **reset** simply inserts a new one. Older messages
  stay in the database (useful for auditing) but are no longer part of the history the
  assistant sees.
- **`messages`** — the single table mandated by the task, storing the full
  conversation history: `user` messages, `assistant` replies, `tool_call` entries
  (which tool was invoked and with what arguments) and `tool_result` entries (what the
  tool returned). Every chat turn re-loads this table from the database (never from
  in-process memory) before calling the LLM, so the assistant is always aware of prior
  messages and prior tool usage — even across backend restarts.

### Request flow

1. `POST /api/chat` persists the user's message, then loads the entire conversation
   history from `messages` and replays it into Gemini's `contents` format.
2. Gemini is called with streaming enabled. Text tokens are forwarded to the client
   immediately as `token` SSE events.
3. If Gemini requests a tool call, the call and its arguments are persisted as a
   `tool_call` row and streamed to the client, the tool is executed in-process against
   `products.json`, and the result is persisted as a `tool_result` row and streamed
   back. The loop then calls Gemini again with the tool result appended, so it can
   produce a final, grounded answer (capped at a few iterations to avoid runaway
   loops).
4. The final assistant reply is persisted and a `done` event closes the stream.

### Tools

The assistant has five tools, so it can pick the most specific one for each question
instead of over-fetching the whole catalog:

- `get_products(category?, max_price?, min_price?, in_stock?, on_discount?, search?, sort_by?, limit?)`
  — flexible catalog search/filter (covers "what do you have", "under 50 EUR", "in
  stock", "on discount", free-text search), with optional sorting and result limiting.
- `get_product_details(product_id?, name?)` — full details (price, specs,
  description) for one specific product.
- `list_categories()` — catalog overview: each category with its product count and
  price range (good for "what kinds of things do you sell?").
- `compare_products(identifiers)` — side-by-side comparison of two or more products by
  id or name (price, discount, rating, stock).
- `recommend_products(max_price?, category?, in_stock_only?, limit?)` — best-rated
  picks within an optional budget/category (for "recommend a gift under €100").

Each tool is defined once as a `Tool` (handler + Gemini `FunctionDeclaration`) in a
single registry in [`product_tools.py`](backend/app/services/product_tools.py), so both
the declarations sent to the model and the dispatch table stay in sync and adding a tool
is a one-line registration rather than a new class hierarchy. The system prompt
instructs the model to only answer product questions using these tools, never from its
own knowledge.

### Frontend / UI

- **Streaming chat** built on a single `useChat` hook that consumes the SSE stream,
  handles token/tool_call/tool_result/done/error events, and supports **stop** (aborts
  the in-flight request) and **reset**.
- **Rich Markdown replies** — the model returns Markdown (bold product names, bullet
  lists, prices), rendered with `react-markdown` + `remark-gfm` and mapped to themed
  components, so answers look like a formatted product list instead of raw asterisks.
- **Tool transparency** — `tool_call` / `tool_result` rows render as compact inline
  activity steps ("Get products · 5 product(s)") so you can watch the assistant look
  things up.
- **Themed after [jannytech.com](https://jannytech.com/)** — Poppins, the green
  (`#06D6A0`) brand palette, 16px card radius, soft shadows, and the signature
  interactive dot-grid background.
- **Edge cases handled** — smart auto-scroll (won't yank you down while reading
  history), suggestion chips on the empty state, client-side length guard, graceful
  error banner, and a responsive full-screen layout on mobile / centered card on
  desktop.

## Design decisions & best practices

- **Layered architecture** — routes → services (LLM/tool orchestration) → repositories
  (DB access) → ORM models. Each layer is independently testable and the HTTP layer
  knows nothing about SQLAlchemy or Gemini specifics.
- **Dependency injection** (FastAPI `Depends`) for the DB session and the LLM client.
  The LLM client is injected via an `LLMClient` protocol, which is what lets the test
  suite swap in a scripted `FakeGeminiClient` and exercise the full tool-calling loop
  deterministically, with no network calls or API key required.
- **Repository pattern** for conversations/messages, isolating SQLAlchemy from the
  rest of the app.
- **Centralized error handling** — a small `AppError` hierarchy plus exception
  handlers for validation errors and unhandled exceptions ensure every failure path
  (empty message, overly long message, LLM failure, etc.) returns a clean JSON error
  body with an appropriate status code instead of a bare 500.
- **Pydantic Settings** for 12-factor configuration (`DATABASE_URL`, `GEMINI_API_KEY`,
  `GEMINI_MODEL`, CORS origins, message length limits).
- **Swagger/OpenAPI docs** come for free from FastAPI; routes are annotated with
  summaries, descriptions and response models for a clean `/docs` page.
- **`Base.metadata.create_all` on startup** instead of Alembic migrations — the
  intentionally simplest option for a project this size. A production system would
  add Alembic migrations as the next step.

## Running tests

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
pytest -v
```

The suite runs against an in-memory SQLite database and a scripted fake Gemini
client, so it's fast and needs no Docker, network access or API key. It covers:

- input validation (empty / whitespace-only / overly long messages → 422, not 500)
- the full tool-calling turn (`user` → `tool_call` → `tool_result` → `assistant` rows
  persisted correctly and returned via `/api/chat/history`)
- a plain (no-tool) chat turn
- reset behavior (history is empty after reset; prior conversation stays in the DB)
- graceful handling of LLM failures (SSE `error` event, not a 500)
- every tool's logic against the real `products.json` (search/sort/limit, details,
  categories, compare, recommend) plus a registry-consistency check that the exposed
  `FunctionDeclaration`s match the dispatch table

## Configuration

All configuration is via environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Description |
| --- | --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `postgres` / `postgres` / `product_assistant` | Postgres credentials, shared by the `db` and `backend` services |
| `GEMINI_API_KEY` | _(empty)_ | Your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Gemini model used for chat + tool calling |

## Notes / possible next steps

- Alembic migrations instead of `create_all` for schema evolution.
- Per-user/session conversations (currently there is a single global "current"
  conversation, matching the scope of the task).
- Rate limiting and retries around the Gemini API call.

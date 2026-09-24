# AGENTS.md — aina-ai-platform (final year project)

## Layout (monorepo, two apps + tiny shared)
- `client/src/` — Vite + React 19 + Tailwind v4 + shadcn (`new-york`/neutral) frontend. Entrypoints: `client/src/main.tsx` → `client/src/App.tsx` (wouter routes, lazy pages in `client/src/pages/`).
- `backend/app/` — FastAPI backend. Entrypoint: `backend/app/main.py` (`app.main:app`). Routers in `backend/app/api/v1/` all under `/api/v1`; models in `backend/app/models/` (registered via `backend/app/db/base.py`); business logic in `backend/app/services/`.
- `shared/const.ts` — trivial constants only, not a real shared package.
- Path aliases (frontend): `@` → `client/src`, `@shared` → `shared`, `@assets` → `attached_assets` (see `vite.config.ts`, `tsconfig.json`).

## Codebase structure (detailed)

Root (frontend workspace + ops):
- `package.json` / `pnpm-lock.yaml` / `patches/wouter@3.7.1.patch` — frontend deps only (backend has its own `backend/requirements.txt`). `vitest` installed but no script wires it.
- `vite.config.ts` — `root: client`, `outDir: dist/public`, aliases `@`/`@shared`/`@assets`, dev port 3000, plus Manus debug-collector/runtime plugins.
- `tsconfig.json` — includes `client/src/**/*`, `shared/**/*`, stale `server/**/*`; `pnpm check` = `tsc --noEmit`.
- `components.json` — shadcn `new-york`, `baseColor: neutral`, aliases `@/components`, `@/lib/utils`, `@/hooks`.
- `Dockerfile` (root, frontend) vs `backend/Dockerfile` (python:3.12-slim, API). `docker-compose.yml` (root: frontend+api+2 workers+db+pgadmin) vs `backend/docker-compose.yml` (api+db+pgadmin only).
- `shared/const.ts` — only `COOKIE_NAME`, `ONE_YEAR_MS`. `client/src/const.ts` is separate frontend constants.
- `docs/` — `authentication/`, `phase4/`, `RAG/`, `system/`, `backend_roadmap.md`, `skills_reference.md` (design prose, not source of truth).

`client/` (Vite root; `index.html` → `/src/main.tsx`):
- `src/main.tsx` — wraps `App` in `GoogleOAuthProvider` (`VITE_GOOGLE_CLIENT_ID`).
- `src/App.tsx` — `ErrorBoundary > AuthProvider > NotificationProvider > ThemeProvider`; public routes (`/`, `/login`, `/signup`, `/forgot-password`, `/reset-password`) + `ProtectedRoute > LayoutProvider > DashboardLayout` wrapping `/dashboard`, `/inbox`, `/builder`, `/analytics`, `/settings`, `/models`. All pages lazy-loaded via `Suspense` + `PageLoader`.
- `src/pages/`:
  - `AinaLanding.tsx` (`/`), `Home.tsx` (legacy/unused variant), `Login.tsx`, `Signup.tsx`, `ForgotPassword.tsx`, `ResetPassword.tsx`, `NotFound.tsx`.
  - `Dashboard.tsx` — KPI + chatbot list (note: hardcodes `localhost:8000`).
  - `Builder/` — 4-step bot wizard: `index.tsx` + `types.ts` + `components/Step1Persona.tsx`, `Step2Knowledge.tsx`, `Step3Test.tsx` (chat simulator), `Step4Deploy.tsx` (emits `widget.js` snippet), `StepBar.tsx`, `ChatSimulator.tsx`.
  - `Inbox.tsx` — human-agent handoff queue (`/api/v1/agents/conversations`, `/reply`, `/resolve`, `/stream`).
  - `Analytics/` — `index.tsx` + `components/GlobalFilters.tsx`, `KPIs.tsx`, `VolumeChart.tsx`, `ChannelPerf.tsx`, `LanguageMix.tsx`, `InteractionsTable.tsx` (all via `api.baseUrl`).
  - `Models/` — `Models.tsx` + `components/ActiveModelsTable.tsx`, `ConfigureModal.tsx`, `RoutingFabric.tsx` (provider configs + intent routing rules).
  - `Settings.tsx` + `Settings/components/ProfileTab.tsx`, `SecurityTab.tsx`, `ApiKeysTab.tsx`, `UsageBillingTab.tsx` (mostly hardcoded `localhost:8000` — fix to `api.baseUrl` when touching).
- `src/components/` — shell: `DashboardLayout.tsx`, `Sidebar.tsx`, `TopBar.tsx`, `ProtectedRoute.tsx`, `ErrorBoundary.tsx`, `PageLoader.tsx`, `MarkdownRenderer.tsx`, `Map.tsx`, `ManusDialog.tsx`; `ui/` = ~45 shadcn primitives (`button`, `dialog`, `form`, `sidebar`, `chart`, `sonner`, …) — do not hand-edit; extend via composition.
- `src/contexts/` — `AuthContext.tsx` (token in `localStorage["token"]`, `unauthorized` listener), `NotificationContext.tsx` (REST + WS; hardcodes `localhost:8000`), `ThemeContext.tsx`, `LayoutContext.tsx`.
- `src/lib/api.ts` — the only correct API client: `API_BASE_URL`, `apiRequest()` (dual overloads, auto `Authorization: Bearer`, 204 handling), `api.baseUrl`, typed `api.*` helpers, SSE stream parsers (`streamBuilderMessage`, `streamConversationEvents`), plus the global 401 `fetch` interceptor. `src/lib/utils.ts` — `cn()` (clsx + tailwind-merge).
- `src/hooks/` (`useMobile.tsx`, `useComposition.ts`, `usePersistFn.ts`), `src/layouts/AuthLayout.tsx`, `src/index.css` (Tailwind v4 entry).

`backend/` (all Python; run from here):
- `app/main.py` — creates `FastAPI(openapi_url=/api/v1/openapi.json)`, mounts 14 routers (see below), CORS (empty `CORS_ORIGINS` → localhost regex), DB-error classifier → 503, `lifespan`: ad-hoc personas DDL + enum creation, `SemanticRouter._initialize` thread, in-process knowledge + message worker threads, APScheduler (hourly analytics aggregation, 30s heartbeats, daily message-job cleanup). Serves `/`, `/health` (db, gemini key, semantic router, 2 worker heartbeats), `/ready`, `/metrics`, `/widget.js` (public chat embed).
- `app/api/deps.py` — `get_current_user` (HTTPBearer JWT), `get_tenant_db`, `get_current_org_id`, API-key auth + `update_api_key_last_used`.
- `app/api/v1/` (prefix mounted in `main.py`): `auth.py` (`/auth`), `users.py` (`/users`), `bots.py` (`/` — personas/chatbots), `models.py` (`/models` — providers/configs/routing), `knowledge.py` (`/knowledge` — sources/upload/validate-url), `messaging.py` (`/chat` — bot chat + SSE streams), `analytics.py` (`/analytics`), `agents.py` (`/agents` — handoff inbox), `channels.py` (`/channels`), `deployments.py` (`/deployments`), `billing.py`, `team.py`, `api_keys.py`, `notifications.py` (last four mounted at `/` with full paths inside).
- `app/core/` — `config.py` (`Settings`, all env incl. RAG/WhatsApp/Firecrawl/TypeSafe tunables), `security.py` (JWT/argon2), `email.py`, `language.py`, `messages.py`, `metrics.py` (prometheus), `circuit_breaker.py`.
- `app/db/` — `session.py` (sync `engine`/`SessionLocal` + async `async_engine`/`AsyncSessionLocal`, `get_db`), `base.py` (imports all models for Alembic), `base_repository.py`.
- `app/models/` — `user.py`, `organization.py` (`Organization`, `OrgMember`), `persona.py`, `chatbot.py`, `ai_model.py` (`AIProvider`, `AIModelConfig`, `RoutingRule`), `document.py` (`KnowledgeSource`, `Document`, `KnowledgeChunk`, `KnowledgeJob`), `conversation.py` (`Deployment`, `Conversation`, `Message`, `ProcessedEvent`), `subscription.py`, `api_key.py`, `notification.py`, `analytics.py`, `semantic_cache.py`, `message_job.py`.
- `app/schemas/` — request/response pydantic per domain: `auth`, `bot`, `chat`, `document`, `analytics`, `api_key`, `billing`, `notification`, `team`, `whatsapp`.
- `app/services/` — `chat.py` (ChatService + `AgentGraphExecutor`, SSE streaming), `rag/graph.py` (LangGraph singleton: route → cache → retrieve → validate → generate, plus handoff/conversational branches), `rag/nodes/` (`routing`, `cache`, `retrieval`, `validation`, `generation`, `rewrite`, `conversational`, `handoff`, `transform`), `rag/{state,retriever,prompts,helpers}.py`, `document.py` (ingestion: upload/URL/crawl → chunk → embed jobs), `chunker.py`, `text_extractor.py` (PDF/DOCX), `embedding.py` (Gemini/OpenRouter/Qwen, batch 64), `vector_store.py` (pgvector, `DENSE_MAX_DISTANCE=0.55`), `semantic_router.py` (tiered intent router + memory thresholds 6/4), `semantic_cache.py`, `escalation_router.py`, `channel_router.py`, `whatsapp.py` (webhook verify + Cloud API), `deployment.py`, `bot.py`, `auth.py`, `team.py`, `billing.py`, `api_key.py`, `notification.py`, `outbox.py` + `message_job` delivery, `streaming.py`, `sse_manager.py`, `pubsub.py` (in-memory default, `REDIS_URL` optional), `websocket.py`, `storage.py`, `report_export.py`, `firecrawl_service.py`.
- `app/workers/` — `knowledge_worker.py` (ingestion queue, stuck-job requeue >30min, `aina_worker_heartbeat`), `message_worker.py` (outbox delivery, `aina_message_worker_heartbeat`). Both run as lifespan threads AND standalone (`python -m app.workers.*` in compose).
- `app/tasks/analytics_aggregation.py` — hourly rollup into `AnalyticsDaily/ByChannel/ByLang` (incl. keyword sentiment incl. Urdu/Roman-Urdu lists).
- `app/templates/email/` — `invite_member.html`, `reset_password.html`.
- `alembic/` — `env.py` (URL from `settings.DATABASE_URL`), ~17 `versions/` (builder integration, multi-tenancy hardening, indexes/PK fix, api-keys/chunks, AI routing, crawl metadata, HNSW index, model override, message jobs, vector-dim 1536→2048, tsvector, persona-trait index, conversation memory, …).
- `tests/` (`requirements-dev.txt`: pytest + pytest-asyncio + httpx) — `test_chat.py`, `test_stream.py`, `test_bots.py`, `test_users_api.py`, `test_agents_routes.py`, `test_chat_session_manager.py`, `test_escalation_router.py`, `test_ingestion_pipeline.py`, `test_rag_utils.py`, `test_prompts_catalog.py`, `test_phase6.py`, `test_phase7.py`, `test_enum.py`, `test_url.py`, `test_whatsapp.py`, `test_crawl_debug.py` (needs network), plus `update_db.py` (legacy DDL helper — not a test) and `verify_pgvector.py` (needs live PG + keys).
- `evals/` — `run_all_evals.py` + `datasets/`, `evaluators/`, `reports/`, `components/` (RAG quality harness, expensive — don't run by default).

## Frontend (root) — use pnpm, not npm
- Package manager is **pnpm** (`packageManager: pnpm@10.4.1`, `pnpm-lock.yaml`). Dockerfile uses `corepack` + `pnpm install --frozen-lockfile`.
- Commands (run from repo root): `pnpm dev` (vite dev, `root: client`, port 3000), `pnpm build` (outputs to `dist/public`), `pnpm check` (`tsc --noEmit`), `pnpm format` (prettier `--write .`).
- Env: `VITE_API_BASE_URL` (defaults to `http://localhost:8000` in `client/src/lib/api.ts`). Root `.env` needs `VITE_GOOGLE_CLIENT_ID`.
- Gotchas: several pages/components **hardcode `http://localhost:8000/…`** instead of using `api.baseUrl` (e.g. `NotificationContext.tsx`, `Dashboard.tsx`, Settings tabs). New code must use `api.baseUrl` / `apiRequest` from `client/src/lib/api.ts`.
- Auth: JWT in `localStorage["token"]`, sent as `Bearer`. Global `fetch` interceptor dispatches `unauthorized` event on 401 for `/api/*` (non-auth) routes — preserve this.
- `wouter@3.7.1` is **patched** (`patches/wouter@3.7.1.patch` via `pnpm.patchedDependencies`). Do not upgrade wouter without regenerating the patch.
- No frontend test/lint scripts exist (`vitest` is installed but unwired). Verify with `pnpm check` + `pnpm build`.

## Backend (in `backend/`) — Python 3.12, FastAPI + Postgres
- Setup: `cd backend && python -m venv venv` (repo already has gitignored `backend/venv`), install `requirements.txt`; dev/test extras in `tests/requirements-dev.txt`. `pytest.ini` sets `pythonpath = .`, so **run pytest from `backend/`**: `python -m pytest tests/test_chat.py -v` (single test), full: `python -m pytest tests/ -v`.
- Tests mock DB/LLM deps (`TestClient` + `dependency_overrides`, `AsyncMock`); most need no live DB, but `verify_pgvector.py` / crawl tests need Postgres + API keys.
- Required env (`backend/.env`, loaded via `pydantic-settings`, `env_file=".env"`): `DATABASE_URL` (sync `postgresql://…` URL; async engine is derived by string-replacing with `postgresql+asyncpg://`) and `SECRET_KEY` (**no fallback — app fails without it**).
- DB engines are dual (see `app/db/session.py`): **sync** `engine`/`SessionLocal` for workers/alembic/health checks, **async** `async_engine`/`AsyncSessionLocal` (`asyncpg`, pool 15+5) for request handlers. Use the matching one.
- Migrations: Alembic in `backend/alembic/` (`env.py` reads `settings.DATABASE_URL`). From `backend/`: `alembic upgrade head`. Note `app/main.py:lifespan` also runs ad-hoc DDL (personas TEXT columns, `enum_message_job_status`) and Docker API runs `python update_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000` — prefer Alembic for schema changes, keep `update_db.py`/lifespan DDL in mind when debugging drift.
- Workers: `app/workers/knowledge_worker.py` + `app/workers/message_worker.py` run **both** as lifespan threads in-process **and** as separate Docker services. They write heartbeat files to `tempdir/aina_*_heartbeat`; `/health` reports `degraded`/503 when heartbeats are stale (>120s) or `GEMINI_API_KEY` missing. Don't "fix" duplicate worker execution without understanding this.
- pgvector note: `EMBEDDING_DIM` default 2048 (comment: HNSW limit 4000); changing embedding model/dim requires a migration, not just config.

## Docker
- Two compose files: root `docker-compose.yml` (frontend :5173, api :8000, knowledge-worker, message-worker, db :5432, pgadmin :5050) vs `backend/docker-compose.yml` (api+db+pgadmin only). Root frontend service mounts `.:/app` and runs `pnpm run dev`. API consumes `backend/.env`; frontend consumes root `.env`.
- CORS: empty `CORS_ORIGINS` = localhost-only regex fallback in `main.py`; set explicit origins in prod.

## Conventions
- Prettier: double quotes, semicolons, 2-space, `arrowParens: avoid` (`.prettierrc`). No ESLint config.
- API prefix is `/api/v1` (`API_V1_STR`); keep `openapi_url` at `/api/v1/openapi.json`. Health: `/health` (deep checks), `/ready`, `/metrics`, `/widget.js` (public embed script served by backend).
- Never commit secrets: `.env`, `data/`, `security_report*.json`, venvs are gitignored (but note: `backend/.env` and root `.env` currently exist on disk — read keys only, don't print values).

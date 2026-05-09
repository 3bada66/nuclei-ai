# Deeply Analytics — Full System Specification

> **Document type.** Architecture and implementation specification for *Deeply Analytics*, a web-first AI microscopy analysis platform built on top of the existing nuclei segmentation and counting pipeline.
> **Status legend.** **[Implemented]** = verified in the repository today · **[Partial]** = exists in skeletal or single-instance form · **[Proposed]** = part of the target architecture, not yet built.
> **Document version.** v0.1 — 2026-05-02.

---

## A. Executive Project Definition

**Deeply Analytics** is a web-first SaaS-style platform for AI-driven microscopy image analysis. It accepts microscopy or histopathology images, runs a U-Net-based nuclei segmentation pipeline, derives quantitative analytics (cell count, morphology, density), and presents the results to users through a responsive React dashboard. The system persists projects, analysis jobs, results, and exports so that users can return to past work, share it, and produce reproducible reports.

**Problem it solves.** Manual nuclei counting and morphology measurement on microscopy images are slow, observer-dependent, and difficult to reproduce. Existing scripted pipelines (including the one currently in this repository at `src/`) produce strong results but only as command-line outputs. They do not scale to multi-user laboratories, do not preserve history, and do not present results in a form that non-technical researchers can consume directly. Deeply Analytics closes that gap by wrapping the AI pipeline in a real software platform: authentication, projects, persistent jobs, structured results, dashboards, and exports.

**Why web-first.** The platform must run anywhere a research browser runs, with no local install, no GPU on the client, and no notebook environment to maintain. A web application is the only delivery model that simultaneously supports multi-user access, central storage of model artefacts, controlled rollout of model updates, and shared institutional history.

---

## B. Final System Goal

Deeply Analytics implements the following end-to-end workflow, executed in sequence for every analysed image:

```
Image upload
   → Preprocessing (resize, normalise, format-check)
   → U-Net inference (PyTorch, ResNet-18 encoder)
   → Postprocessing (sigmoid + threshold, connected components)
   → Nuclei counting
   → Morphology / density analytics
   → Result storage (DB + object storage)
   → Dashboard visualisation
   → Export / report (CSV, PNG, PDF)
```

This is a **real software system**, not just an AI model:

- The model is one component among many; auth, persistence, jobs, exports, and UI are equally important.
- The system holds state across sessions: users, projects, jobs, results, and exported artefacts.
- Long-running inference is an asynchronous job, not a blocking HTTP call.
- The dashboard is a navigable application with multiple pages, not a single upload demo.
- Operations are governed by validation, authorisation, and observable runtime metrics.

The presence of the AI pipeline strengthens the product but does not define its boundary. The boundary is the platform that *uses* the AI to deliver reliable analytics with a defensible audit trail.

---

## C. Software Architecture

Deeply Analytics is built on a **layered architecture**. Each layer has one responsibility, exposes a narrow contract to the next layer up, and depends only on layers below it.

### C.1 Presentation layer (React + Vite + TypeScript)

- **Responsibilities.** Render pages, manage UI state, handle user input, talk to the API over HTTPS, format responses for human consumption.
- **Main modules.** Pages (`Login`, `Dashboard`, `New Analysis`, `Analysis Result`, `Analysis History`, `Reports`, `Settings`); reusable components (KPI cards, tables, modals, tabs, charts, upload zones); the API client; the authentication context; the routing tree.
- **Connection.** Calls the API layer over `fetch` (today) or TanStack Query (proposed). Carries a JWT in the `Authorization` header for protected routes.
- **Status.** **[Partial]** — single-page MVP UI in `frontend/src/` (Upload + Result + Workflow). The 7 official pages, sidebar, and dashboard layout are **[Proposed]**.

### C.2 API layer (FastAPI)

- **Responsibilities.** Accept HTTP requests, validate inputs and outputs, authenticate the caller, route the request to the right service, return correct HTTP status codes.
- **Main modules.** `routers/auth.py`, `routers/projects.py`, `routers/analyses.py`, `routers/results.py`, `routers/reports.py`, `dependencies/auth.py` (JWT decoder), `middleware/cors.py`, `middleware/rate_limit.py`.
- **Connection.** Receives JSON or multipart from the frontend, calls a single service per request, returns Pydantic models.
- **Status.** **[Partial]** — `backend/main.py` exists today with `/api/health`, `/api/analyze`, `/files/{name}`. Routers per resource are **[Proposed]**; auth/middleware are **[Proposed]**.

### C.3 Service layer

- **Responsibilities.** Orchestrate the workflow. Hold the business rules (e.g. *only the owner may export a result*, *export is allowed only after a job is completed*). Combine repository calls and AI calls into one transactional outcome.
- **Main modules.** `services/auth_service.py`, `services/project_service.py`, `services/analysis_service.py` (already exists), `services/result_service.py`, `services/export_service.py`, `services/notification_service.py`.
- **Connection.** Called by routers; calls the data access layer and the AI inference layer; never touches HTTP or SQL directly.
- **Status.** **[Partial]** — `backend/services/analysis_service.py` exists for live U-Net inference. The other services are **[Proposed]**.

### C.4 Data access layer

- **Responsibilities.** Translate domain operations into database queries. Hide SQL behind repositories. Manage transactions.
- **Main modules.** `db/session.py` (engine + session factory), `db/models/` (SQLModel/SQLAlchemy classes), `db/repositories/` (one per aggregate: `users`, `projects`, `analyses`, `results`, `exports`).
- **Connection.** Called only by services. Owns Alembic migrations under `db/migrations/`.
- **Status.** **[Proposed]** — no database, no ORM, no migrations exist today.

### C.5 AI inference layer

- **Responsibilities.** Pure model logic. Load the U-Net checkpoint, run preprocessing → inference → postprocessing, expose deterministic Python functions to the service layer. No HTTP, no DB, no auth.
- **Main modules.** `src/infer.py` (`make_overlay`, model loading), `src/batch_count_refined.py` (`count_nuclei_from_binary`), `src/extract_morphology.py`, `src/generate_density_maps.py`, plus the proposed `preprocess.py`, `postprocess.py` extraction (Section J).
- **Connection.** Imported by `services/analysis_service.py` (already wired). Reads the checkpoint at `outputs/checkpoints/best_model.pth`.
- **Status.** **[Implemented]** — the U-Net pipeline, the trained checkpoint, the counter, the morphology extractor, and the density-map generator all exist and are verified.

---

## D. Full System Connection Flow

The end-to-end path of one analysis from browser to backend to AI and back:

| # | Step | What happens | Status |
|---|---|---|---|
| 1 | **User opens frontend** | Vite-served React app loads at `https://deeply-analytics.app`. Public routes (Login) render; protected routes redirect if no JWT. | [Partial] — app loads at `http://127.0.0.1:5173/` today; routing is single-page. |
| 2 | **User logs in** | `POST /auth/login` returns a JWT; frontend stores it in memory + httpOnly cookie. | [Proposed] |
| 3 | **User uploads image** | Frontend sends `multipart/form-data` to `POST /analyses/upload`. The image is stored under `storage/uploads/{job_id}.{ext}`. | [Partial] — `POST /api/analyze` already accepts uploads and saves to `backend/storage/uploads/`. The session-bound `/analyses/upload` endpoint is [Proposed]. |
| 4 | **Backend stores image and creates analysis job** | A new `analysis_jobs` row is inserted with status `pending`. Service returns `job_id` immediately. | [Proposed] — current MVP runs synchronously. |
| 5 | **Background task executes inference** | A worker (FastAPI BackgroundTasks for MVP, Celery/RQ in production) loads the model, runs preprocessing → inference → postprocessing → counting → morphology → density, writes artefacts to object storage, persists `analysis_results` and `morphology_records`, marks the job `completed`. | [Partial] — synchronous version of this pipeline runs today inside the request. Asynchronous job handling is [Proposed]. |
| 6 | **Results are stored** | Structured numeric results in PostgreSQL (`analysis_results`, `morphology_records`). Binary artefacts (mask, overlay, density heatmap) in object storage. | [Partial] — files written to `backend/storage/results/` today; DB persistence is [Proposed]. |
| 7 | **Frontend polls/fetches status** | Result page calls `GET /analyses/{id}/status` until status is `completed` or `failed`. | [Proposed] |
| 8 | **Result page renders analytics** | The page calls `GET /results/{id}`, `GET /results/{id}/morphology`, `GET /results/{id}/density`, and renders three image cards, a count tile, a morphology table, and a density heatmap. | [Partial] — single-call rendering exists today; the multi-endpoint result composition is [Proposed]. |
| 9 | **History and reports reuse saved data** | History page lists past jobs; reports/export page generates CSV / PNG / PDF on demand from stored data. | [Proposed] |

---

## E. Frontend Architecture

### E.1 Folder structure (proposed)

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── public/
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── routes.tsx
    ├── api/
    │   ├── client.ts            # fetch wrapper, auth header injection
    │   ├── auth.ts
    │   ├── projects.ts
    │   ├── analyses.ts
    │   ├── results.ts
    │   └── reports.ts
    ├── pages/
    │   ├── Login.tsx
    │   ├── Dashboard.tsx
    │   ├── NewAnalysis.tsx
    │   ├── AnalysisResult.tsx
    │   ├── AnalysisHistory.tsx
    │   ├── Reports.tsx
    │   └── Settings.tsx
    ├── components/
    │   ├── layout/
    │   │   ├── AppShell.tsx     # sidebar + header + outlet
    │   │   ├── Sidebar.tsx
    │   │   └── TopHeader.tsx
    │   ├── kpi/
    │   │   ├── KpiCard.tsx
    │   │   └── KpiGrid.tsx
    │   ├── upload/
    │   │   ├── UploadPanel.tsx
    │   │   └── FilePreview.tsx
    │   ├── result/
    │   │   ├── ResultViewer.tsx
    │   │   ├── MaskOverlayTabs.tsx
    │   │   └── MorphologyTable.tsx
    │   ├── history/
    │   │   ├── HistoryTable.tsx
    │   │   └── HistoryFilters.tsx
    │   ├── modals/
    │   │   └── ConfirmModal.tsx
    │   ├── feedback/
    │   │   ├── EmptyState.tsx
    │   │   ├── ErrorState.tsx
    │   │   └── Skeleton.tsx
    │   └── workflow/
    │       └── WorkflowSteps.tsx
    ├── hooks/
    │   ├── useAuth.ts
    │   ├── useAnalysisJob.ts    # polls status until terminal
    │   ├── useDebounce.ts
    │   └── useMediaQuery.ts
    ├── context/
    │   └── AuthContext.tsx
    ├── types/
    │   ├── auth.ts
    │   ├── project.ts
    │   ├── analysis.ts
    │   └── result.ts
    ├── lib/
    │   ├── format.ts
    │   └── motion.ts            # shared Framer Motion variants
    └── styles/
        ├── tokens.css
        └── globals.css
```

### E.2 Pages

| # | Page | Purpose | Key UI sections | Primary components | Backend endpoints | User actions | Status |
|---|---|---|---|---|---|---|---|
| 1 | **Login** | Authenticate the user | Centred card, email + password, error state, link to register | `Login.tsx`, `AuthContext` | `POST /auth/login` | Sign in, switch to register | [Proposed] |
| 2 | **Dashboard** | Single-screen overview of recent activity and KPIs | KPI grid (jobs this week, average count, median MAE, storage used), recent jobs table, quick "New analysis" CTA | `KpiGrid`, `HistoryTable`, `WorkflowSteps` | `GET /analyses/history`, `GET /projects` | Open a recent job, start a new analysis | [Proposed] |
| 3 | **New Analysis / Upload** | Submit a microscopy image | Project selector, drag-and-drop upload, parameter form (threshold, min_area), "Run analysis" CTA | `UploadPanel`, `FilePreview` | `POST /analyses/upload`, `POST /analyses/start` | Pick project, upload, set parameters, start | [Partial] — single upload page exists today |
| 4 | **Analysis Result** | Show the output of a single job | Tabs: Overlay, Mask, Density, Morphology; KPI tiles (count, processing time, mode); export button | `ResultViewer`, `MaskOverlayTabs`, `MorphologyTable` | `GET /analyses/{id}`, `GET /results/{id}/morphology`, `GET /results/{id}/density` | Switch tab, export, return to history | [Partial] |
| 5 | **Analysis History** | Browse all past analyses | Filter bar (project, date, status), paginated table, row click to open result | `HistoryTable`, `HistoryFilters` | `GET /analyses/history` (filtered) | Filter, sort, paginate, open | [Proposed] |
| 6 | **Reports / Export** | Generate downloadable reports | Selectable analyses, export format (CSV/PNG/PDF), recent exports list | `HistoryTable`, modal with format chooser | `POST /reports/{id}/export-csv`, `-png`, `-pdf` | Trigger export, download artefact | [Proposed] |
| 7 | **Settings / Admin** | Manage account and (admin) users/roles | Tabs: Profile, Security (change password), Admin (users, roles, rate limits) | Standard form components | `GET /auth/me`, admin CRUD endpoints | Update profile, change password, manage users (admin only) | [Proposed] |

### E.3 Layout strategy

- **Fixed sidebar** with collapsible labels at narrow widths; primary nav: Dashboard, New Analysis, History, Reports, Settings.
- **Top header** with breadcrumb, project switcher, user menu, and a global "New analysis" button.
- **Content area** uses a 12-column grid; KPIs span 3 columns each; tables span the full row.
- **Loading / empty / error states** are first-class components, never an undefined screen.
- **Tabs** for the result page so the user can move between overlay/mask/density/morphology without page reloads.
- **Charts** rendered with a small library (e.g. Recharts or Chart.js) for morphology distributions and density summaries.

---

## F. Backend Architecture

### F.1 Folder structure (proposed)

```
backend/
├── main.py                       # FastAPI app, includes routers, middleware
├── config.py                     # pydantic-settings, env-driven config
├── dependencies/
│   ├── auth.py                   # JWT decode, current_user, require_role
│   └── pagination.py
├── middleware/
│   ├── cors.py
│   ├── rate_limit.py
│   └── error_handlers.py
├── routers/
│   ├── auth.py
│   ├── projects.py
│   ├── analyses.py
│   ├── results.py
│   └── reports.py
├── schemas/                      # Pydantic models (request/response)
│   ├── auth.py
│   ├── project.py
│   ├── analysis.py
│   ├── result.py
│   └── report.py
├── services/
│   ├── auth_service.py
│   ├── project_service.py
│   ├── analysis_service.py       # exists today (live U-Net wrapper)
│   ├── result_service.py
│   └── export_service.py
├── db/
│   ├── session.py
│   ├── models/
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── analysis_job.py
│   │   ├── analysis_result.py
│   │   ├── morphology_record.py
│   │   └── export.py
│   ├── repositories/
│   │   ├── users.py
│   │   ├── projects.py
│   │   ├── analyses.py
│   │   ├── results.py
│   │   └── exports.py
│   └── migrations/               # Alembic
├── ai/                           # thin re-export wrappers around src/
│   ├── preprocess.py
│   ├── infer.py
│   ├── postprocess.py
│   ├── count.py
│   ├── morphology.py
│   └── density.py
├── workers/
│   ├── tasks.py                  # job entry point
│   └── runner.py                 # Celery/RQ bootstrap (or BackgroundTasks)
└── storage/
    ├── uploads/
    └── results/
```

### F.2 Why thin routes / fat services

- **Thin routes.** A router function only translates HTTP into a service call. It validates the request via Pydantic, resolves the current user via a dependency, calls **one** service method, and returns the result. It does not contain business logic.
- **Fat services.** All business rules live in services (e.g. *only completed analyses can be exported*, *a user may not view another user's private result unless admin*). Services are pure Python, easy to unit-test with pytest, and reusable from background workers and admin scripts.
- **Schema validation.** Pydantic enforces field types and constraints at the API boundary before any service code runs. This keeps services free of defensive parsing.
- **Separation of business logic.** Database access lives in repositories, AI logic lives in `ai/` (or `src/`), HTTP lives in routers. Each can change independently.

---

## G. Database Design

PostgreSQL stores **structured metadata**: users, projects, jobs, results, morphology rows, exports. Object storage (local volume in dev, S3-compatible in production) holds **binary artefacts**: original images, masks, overlays, density heatmaps, exported PDFs/PNGs/CSVs. The database stores **paths or object keys**, never the binary content.

### G.1 Tables

| Table | Purpose | Key fields | Relationships |
|---|---|---|---|
| **users** | Account record | `id`, `email` (unique), `password_hash`, `role` (`user`\|`admin`), `created_at` | 1 user → many projects, many analyses, many exports |
| **projects** | Logical grouping of analyses (e.g. study, dataset) | `id`, `owner_id` (FK users), `name`, `description`, `created_at` | 1 project → many `analysis_jobs` |
| **analysis_jobs** | One submission of one image | `id`, `project_id` (FK), `owner_id` (FK), `status` (`pending`\|`processing`\|`completed`\|`failed`), `input_path`, `parameters` (JSONB: threshold, min_area, image_size), `started_at`, `finished_at`, `error_message` | 1 job → 0..1 `analysis_results` |
| **analysis_results** | The numeric and image outcome of one job | `id`, `job_id` (FK, **unique** = one-to-one), `cell_count`, `mode`, `mask_path`, `overlay_path`, `density_path`, `processing_ms`, `created_at` | 1 result → many `morphology_records` |
| **morphology_records** | One row per detected nucleus | `id`, `result_id` (FK), `nucleus_index`, `area`, `perimeter`, `circularity`, `eccentricity`, `centroid_x`, `centroid_y` | many rows per result |
| **exports** | A generated CSV/PNG/PDF artefact | `id`, `result_id` (FK), `owner_id` (FK), `format` (`csv`\|`png`\|`pdf`), `path`, `created_at` | many exports per result |

### G.2 Relationships

- **One-to-many.** `users → projects`, `users → analysis_jobs`, `users → exports`, `projects → analysis_jobs`, `analysis_results → morphology_records`, `analysis_results → exports`.
- **One-to-one.** `analysis_jobs → analysis_results` (a job produces at most one result; enforced with a `UNIQUE` constraint on `analysis_results.job_id`).

### G.3 What goes where

| Data | Store | Reason |
|---|---|---|
| User email, password hash, role | PostgreSQL | Relational integrity, search, RBAC |
| Project name, description | PostgreSQL | Searchable, shared metadata |
| Job status, parameters, timestamps | PostgreSQL | Transactional state, polling |
| Cell count, processing_ms, mode | PostgreSQL | Aggregatable, queryable |
| Per-nucleus morphology rows | PostgreSQL | Aggregatable; tens to thousands of rows per image is acceptable |
| Original image | Object storage | Large binary, immutable, served as a file |
| Predicted mask, overlay, density heatmap | Object storage | Large binaries derived from input |
| Exported CSV / PNG / PDF | Object storage | Immutable binaries downloaded by users |
| References to all binaries | PostgreSQL (`*_path`) | The DB knows where each artefact lives |

**Status: [Proposed]** — no database exists today.

---

## H. REST API Design

All endpoints accept and return JSON, except `POST /analyses/upload` which is `multipart/form-data`. All protected endpoints require an `Authorization: Bearer <jwt>` header.

### H.1 Endpoint summary

| Group | Method | Path | Purpose | Auth | Body | Status |
|---|---|---|---|---|---|---|
| Auth | POST | `/auth/login` | Exchange credentials for a JWT | — | `{email, password}` | [Proposed] |
| Auth | POST | `/auth/register` | Create an account | — | `{email, password}` | [Proposed] |
| Auth | GET | `/auth/me` | Current user profile | yes | — | [Proposed] |
| Projects | GET | `/projects` | List user's projects | yes | — | [Proposed] |
| Projects | POST | `/projects` | Create a project | yes | `{name, description?}` | [Proposed] |
| Projects | GET | `/projects/{id}` | Project detail | yes (owner/admin) | — | [Proposed] |
| Analyses | POST | `/analyses/upload` | Upload an image, create a job | yes | multipart `file`, `project_id`, optional `threshold`, `min_area` | [Partial] — `/api/analyze` exists; new endpoint adds project_id and async job |
| Analyses | POST | `/analyses/start` | Start (or restart) inference for an existing pending job | yes (owner) | `{job_id}` | [Proposed] |
| Analyses | GET | `/analyses/{id}` | Job detail (status, parameters, links) | yes (owner/admin) | — | [Proposed] |
| Analyses | GET | `/analyses/{id}/status` | Lightweight polling endpoint | yes (owner/admin) | — | [Proposed] |
| Analyses | GET | `/analyses/history` | Paginated history with filters | yes | query: `project_id?`, `status?`, `from?`, `to?`, `page`, `page_size` | [Proposed] |
| Results | GET | `/results/{id}` | Result summary (count, paths, metadata) | yes (owner/admin) | — | [Partial] |
| Results | GET | `/results/{id}/overlay` | Overlay image binary | yes (owner/admin) | — | [Partial] — served by `/files/{name}` today |
| Results | GET | `/results/{id}/morphology` | Morphology rows + summary | yes (owner/admin) | — | [Proposed] |
| Results | GET | `/results/{id}/density` | Density heatmap binary | yes (owner/admin) | — | [Proposed] |
| Reports | POST | `/reports/{id}/export-csv` | Generate CSV export | yes (owner/admin) | — | [Proposed] |
| Reports | POST | `/reports/{id}/export-png` | Generate PNG export | yes (owner/admin) | — | [Proposed] |
| Reports | POST | `/reports/{id}/export-pdf` | Generate PDF export | yes (owner/admin) | — | [Proposed] |

### H.2 Request and response types

- **Login response:** `{access_token: string, token_type: "bearer", user: {id, email, role}}`.
- **Project list response:** `[{id, name, description, created_at, job_count}]`.
- **Upload response:** `{job_id, status: "pending", project_id, created_at}` — returns immediately; do not block on inference.
- **Status response:** `{job_id, status: "pending"|"processing"|"completed"|"failed", progress?: number, error?: string}`.
- **Result response:** `{id, job_id, cell_count, mode, processing_ms, image_size, links: {original, mask, overlay, density}, created_at}`.
- **Morphology response:** `{summary: {count, mean_area, mean_circularity, mean_eccentricity}, rows: [{nucleus_index, area, perimeter, circularity, eccentricity, centroid_x, centroid_y}]}`.

### H.3 JSON vs multipart

Use **multipart** only for the upload (`POST /analyses/upload`) — the request carries an image file. Every other endpoint uses **JSON** for both request and response, including the export endpoints which return JSON descriptors with a `download_url` pointing to object storage.

### H.4 HTTP status codes

| Situation | Code |
|---|---|
| Success with body | `200 OK` |
| Resource created | `201 Created` |
| Async job accepted | `202 Accepted` |
| Validation failure (malformed body, wrong type, file too large) | `400 Bad Request` (file size: `413` if oversized) |
| Missing or invalid JWT | `401 Unauthorized` |
| Authenticated but not allowed (e.g. another user's result) | `403 Forbidden` |
| Resource not found | `404 Not Found` |
| Conflict (e.g. starting an already-completed job) | `409 Conflict` |
| Rate limit exceeded | `429 Too Many Requests` |
| Server / inference failure | `500 Internal Server Error` |

### H.5 Common validation and authorisation failures

- **Validation:** missing `project_id` on upload; non-image content type; file > 25 MB; `threshold` outside `[0, 1]`; `min_area` < 0.
- **Authorisation:** requesting `/results/{id}` belonging to another user (returns `403`); calling `/auth/me` without a token (`401`); admin-only routes hit by a regular user (`403`).

---

## I. Validation and Business Rules

### I.1 Pydantic schemas (representative)

```python
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)

class AnalysisStart(BaseModel):
    project_id: int
    threshold: float = Field(ge=0.0, le=1.0, default=0.8)
    min_area: int = Field(ge=0, le=10_000, default=1)

class ExportRequest(BaseModel):
    format: Literal["csv", "png", "pdf"]
```

### I.2 Field constraints

| Field | Rule |
|---|---|
| `email` | RFC-5322-ish, max 254 chars, lowercased on save |
| `password` | min 10 chars, must contain at least one digit and one letter |
| `project.name` | 1–120 chars, trimmed, unique per owner |
| Upload `Content-Type` | `image/png`, `image/jpeg`, `image/tiff`, `image/bmp` |
| Upload size | ≤ 25 MB; reject with `413` otherwise |
| `threshold` | `0.0 ≤ threshold ≤ 1.0` |
| `min_area` | `0 ≤ min_area ≤ 10000` |

### I.3 Service-level rules

- **Project name required** — enforced both at the schema and the service (which also checks per-owner uniqueness).
- **Only valid image formats accepted** — enforced at the router by content type and at the service by `cv2.imdecode` returning non-None.
- **Max upload size** — enforced by middleware; the route never sees oversized payloads.
- **Threshold range** — schema-level; rejected before the service runs.
- **Only owner/admin can access a private result** — enforced in `result_service.get(id, user)`. If `user.id != result.owner_id and user.role != "admin"`, raise `Forbidden`.
- **Export allowed only after analysis is completed** — `export_service.create(result_id, user)` checks `job.status == "completed"`; otherwise `Conflict (409)`.
- **Re-running a completed job** — disallowed; create a new job instead.

### I.4 Meaningful HTTP errors

Errors return `{detail: string, code?: string}` with a code that the frontend can translate into user-friendly text (e.g. `image_too_large`, `unsupported_format`, `result_not_ready`).

---

## J. AI Module Design

The AI layer is intentionally separate from API and UI. It is pure Python with no FastAPI imports, no DB calls, and no auth.

### J.1 Modules

| Module | Responsibility | Input | Output | Connection |
|---|---|---|---|---|
| **preprocess.py** | Decode bytes → RGB uint8 → resize to model input → normalise to `[0,1]` → tensor | `bytes` (image), `target_size: int` | `np.ndarray` (RGB uint8 256×256), `torch.Tensor` (1×3×256×256) | First step in the pipeline; called by the service before inference. **[Partial]** — equivalent logic exists inline in `src/infer.py:load_image` and `backend/services/analysis_service.py:_decode_image`. |
| **infer.py** | Load the U-Net checkpoint (lazy singleton), run forward pass, return raw logits or sigmoid probabilities | `torch.Tensor` (1×3×H×W) | `np.ndarray` (H×W float32 in `[0,1]`) | Second step. **[Implemented]** — `src/infer.py` loads `best_model.pth` and runs the model. |
| **postprocess.py** | Threshold the probability map, clean small artefacts | `np.ndarray` (probabilities), `threshold: float`, `min_area: int` | `np.ndarray` (binary uint8 mask, 0 or 255) | Third step. **[Partial]** — thresholding done inline in `src/infer.py` and the service. Should be extracted into its own module. |
| **count.py** | Connected-component counting | binary mask, `min_area` | `int` (cell count) | Fourth step. **[Implemented]** — `count_nuclei_from_binary` in `src/batch_count_refined.py`. |
| **morphology.py** | Per-nucleus features (area, perimeter, circularity, eccentricity, centroid) | binary mask | list of feature dicts + summary | Fifth step. **[Implemented]** — `src/extract_morphology.py`. |
| **density.py** | Grid-based density heatmap | binary mask, image shape, grid size | `np.ndarray` (heatmap) + PNG | Sixth step. **[Implemented]** — `src/generate_density_maps.py`. |

### J.2 Pipeline contract

```
preprocess(bytes)       -> rgb_image, tensor
infer(tensor)           -> probability_map
postprocess(probs, t)   -> binary_mask
count(mask, min_area)   -> cell_count
morphology(mask)        -> rows, summary
density(mask, shape)    -> heatmap_array, heatmap_png_bytes
```

The service composes these calls in order and persists the artefacts. Each module is independently testable.

---

## K. Background Processing Strategy

Inference for one image takes hundreds of milliseconds on CPU and longer on larger images or under load. Synchronous request handling does not scale: the HTTP connection stays open, the worker is blocked, and a slow upload can stall the API. Therefore inference must run on a background worker.

### K.1 Job lifecycle

```
pending  ───►  processing  ───►  completed
                     │
                     └──►  failed (with error_message)
```

- **pending.** Row inserted by the upload endpoint. Worker has not picked it up yet.
- **processing.** Worker has begun. `started_at` is set.
- **completed.** Worker finished, results persisted, artefacts stored. `finished_at` is set.
- **failed.** Worker raised; `error_message` captures the exception class and message; user can retry by creating a new job.

### K.2 Implementation options

| Option | When to use | Pros | Cons |
|---|---|---|---|
| **FastAPI `BackgroundTasks`** | MVP, single-process deployment, low concurrency | Zero infra, ships with FastAPI, easy to wire in a service | In-process; killed if the API restarts; no retries; no cross-process queue |
| **Celery + Redis broker** | Production with multiple workers, retries, scheduled tasks | Mature, observable (Flower, Prometheus exporters), retries and rate limits built-in | More moving parts; requires Redis or RabbitMQ |
| **RQ (Redis Queue)** | Smaller production deployments | Simpler than Celery, Python-native | Less feature-rich; fewer integrations |

### K.3 Why background jobs matter for AI

- **Latency isolation.** A slow inference cannot drag down unrelated API calls.
- **Concurrency control.** Workers can be capped at the number of GPU slots or CPU cores; the API stays elastic.
- **Failure recovery.** Failed jobs surface as `failed` rows the user can see, retry, or report — not as 500s lost in the logs.
- **Backpressure.** Queue length becomes a monitorable metric (already specified in `TECHNICAL_MONITORING_PLAN.md`).

**Status:** **[Proposed]** — current MVP runs inference synchronously inside `POST /api/analyze`.

---

## L. Animation Strategy for the Website

### L.1 Why Framer Motion

- **First-class React integration.** Components like `<motion.div>` plug into JSX without imperative DOM code.
- **Variants and orchestration.** Staggered children, exit animations, and shared-layout transitions are declarative.
- **AnimatePresence.** Component unmount animations are correct without manual lifecycle management.
- **Accessibility.** Respects `prefers-reduced-motion` out of the box when configured.
- **Performance.** Uses `transform` and `opacity`, the GPU-friendly properties.

### L.2 When to use Framer Motion vs. plain CSS

| Use Framer Motion | Use plain CSS transitions |
|---|---|
| Page-level enter/exit transitions | Hover colour or shadow change on a card |
| Sequenced reveals (e.g. KPI cards staggered in) | Single-property fade or scale on hover |
| Modal / drawer enter/exit with overlay | Active state on a button |
| Result tab content swap with shared layout | Focus ring on inputs |
| Skeleton loaders that depend on data state | Pure decorative pulses |

If a transition is one property and one trigger, CSS is enough. If it involves coordination across several elements or dependencies on app state, use Framer Motion.

### L.3 Where to animate

**Recommended:**

- Login page entrance (form fades up)
- Sidebar appearance on mobile (slide-in)
- KPI card reveal on dashboard (staggered)
- Upload area hover state (subtle elevation)
- Progress bar during analysis (deterministic when known, indeterminate shimmer otherwise)
- Result reveal when status flips to `completed`
- Result tab switching (cross-fade)
- Modal open/close (fade + scale)
- Table row hover (colour only)
- Export success toast (slide-in, auto-dismiss)
- Skeleton loaders while data is fetching

**Avoid:**

- Animating every paragraph or heading
- Animating every icon
- Animating every table cell (kills scroll performance)
- Heavy particle systems
- Looping infinite effects that distract from the data

### L.4 Per-surface animation plans

- **Dashboard cards.** Stagger fade-up (0.04 s delay between cards) on first mount; no animation on data refresh — only the changed numbers update.
- **Upload box.** Hover bumps `scale: 1.01` and the shadow scale; on drag-over, the border colour transitions and the background lightens.
- **Result page.** When `status` becomes `completed`, the three image tiles fade up sequentially; the count tile's number animates from 0 to its final value over 600 ms.
- **Modal.** `AnimatePresence` wraps the modal; backdrop fades; modal scales from 0.96 → 1.
- **Route transitions.** A short cross-fade (120–160 ms) between pages; no slide, which conflicts with browser back navigation.

### L.5 Code examples

**Animated card.**

```tsx
import { motion } from "framer-motion";

export function AnimatedCard({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="card"
    >
      {children}
    </motion.div>
  );
}
```

**Staggered KPI cards.**

```tsx
import { motion } from "framer-motion";

const container = {
  hidden: { opacity: 1 },
  show: { opacity: 1, transition: { staggerChildren: 0.04 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: "easeOut" } },
};

export function KpiGrid({ kpis }: { kpis: { label: string; value: string }[] }) {
  return (
    <motion.div className="kpi-grid" variants={container} initial="hidden" animate="show">
      {kpis.map((k) => (
        <motion.div key={k.label} className="card" variants={item}>
          <h3>{k.label}</h3>
          <div className="metric-value">{k.value}</div>
        </motion.div>
      ))}
    </motion.div>
  );
}
```

**Modal with `AnimatePresence`.**

```tsx
import { AnimatePresence, motion } from "framer-motion";

export function Modal({ open, onClose, children }: ModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="modal-card"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

**CSS fallback for hover/fade.**

```css
.card {
  transition: box-shadow 200ms ease-out, transform 150ms ease-out;
}
.card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-1px);
}
```

**Status:** **[Proposed]** — Framer Motion is not currently a dependency.

---

## M. UI / UX Recommendations

### M.1 Colour palette (light theme, professional SaaS)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#f8fafc` | Page background |
| `--card` | `#ffffff` | Cards, modals, sidebar |
| `--text` | `#1e293b` | Primary text |
| `--text-muted` | `#64748b` | Secondary text |
| `--primary` | `#2563eb` | Primary CTAs, active links |
| `--secondary` | `#7c3aed` | Accents, charts |
| `--success` | `#16a34a` | Status: completed |
| `--warning` | `#f59e0b` | Status: processing, fallback mode |
| `--error` | `#dc2626` | Status: failed |
| `--border` | `#e2e8f0` | Card and input borders |

The current MVP uses a darker design language tied to the "3D-inspired" report; the production palette above is the recommended **default** for the SaaS dashboard. Both can coexist: light theme for the application, deep theme for marketing surfaces.

### M.2 Typography

- Family: **Inter** (already in the MVP), system fallbacks.
- Sizes: 13 / 14 / 16 / 20 / 24 / 32 px. No more than six steps.
- Numbers in metric tiles use `font-variant-numeric: tabular-nums`.

### M.3 Spacing

- 4 px base; allowed steps: 4, 8, 12, 16, 24, 32, 48, 64.
- Cards: 24 px internal padding; KPI cards: 20 px.
- Page gutter: 24 px on desktop, 16 px on tablet, 12 px on mobile.

### M.4 Visual hierarchy

- One primary CTA per page (e.g. "New analysis" on Dashboard).
- KPI numbers larger than their labels.
- Subdued borders, never heavy 1.5–2 px rules.
- Status pills coloured by semantic state, not by aesthetics.

### M.5 Chart presentation

- One concept per chart; never stack two y-axes unless absolutely necessary.
- Use neutral grid lines and a single accent for the primary series.
- Density heatmap rendered with a single perceptually uniform colourmap (e.g. `viridis`).

### M.6 Result readability

- Original / mask / overlay shown side-by-side at the same width so the eye can compare.
- Cell count is the single biggest number on the page.
- Morphology table paginated, sortable, with mean/median in the header.

### M.7 Upload flow UX

1. Empty state with a dashed drop zone and a single line of instruction.
2. On file selection, show a preview within 100 ms.
3. Disable "Run analysis" until a file is present.
4. While analysing, show a workflow bar (Upload → Segment → Count → Report) and a deterministic progress bar if the backend reports progress.

### M.8 Error / empty / loading / progress states

- **Empty.** A single icon, one short sentence, and one CTA. No "no data" with nothing else on the screen.
- **Error.** One short sentence, the underlying code (e.g. `image_too_large`), and a "Try again" CTA.
- **Loading.** Skeletons sized to the eventual content; never a spinner alone for slow loads.
- **Progress.** Deterministic when known; indeterminate shimmer when not. Always visible during inference.

---

## N. State Management Recommendation

### N.1 MVP — local React state + an API layer

For the current scope (one user, a few pages, low data volume), keep state where it is consumed:

- `useState` for form fields, modal visibility, file selection.
- `useEffect` for one-shot fetches.
- A single API module (`src/api/`) that wraps `fetch` and injects the JWT.

This is the pattern already used in the MVP frontend (`frontend/src/api.ts`, local component state). It is sufficient for **[Implemented]** today.

### N.2 Stronger — TanStack Query (React Query)

Once the app grows beyond a handful of pages, switch to **TanStack Query** for server state.

| Reason | Benefit |
|---|---|
| **Caching** | The same `GET /analyses/history` does not refetch on every page mount |
| **Background refetch** | Stale-while-revalidate keeps lists fresh without manual logic |
| **Polling** | `useQuery` with `refetchInterval` is the cleanest way to poll job status |
| **Mutations + invalidation** | After a `POST /analyses/upload`, invalidate the history query so the new job appears |
| **Devtools** | Inspect cache, request timing, and stale state visually |

Keep client-only state (modal open/close, form values) in React state. Server data goes through React Query.

**Status:** **[Proposed]** — not currently a dependency.

---

## O. Testing Strategy

### O.1 Backend — pytest

| Suite | Coverage |
|---|---|
| **Auth tests** | Register valid/invalid; login success/failure; expired token; `/auth/me` requires token |
| **Upload validation tests** | Reject non-image content type, oversized files, missing project_id, invalid threshold |
| **Analysis creation tests** | A valid upload creates a `pending` job; subsequent worker run flips it to `completed` |
| **Result retrieval tests** | Owner can fetch result; another user gets `403`; admin can fetch any result |
| **Export tests** | CSV export schema is correct; PNG export returns the heatmap; PDF export bundles all artefacts; export rejected if job not completed |
| **Permission tests** | Cross-user access patterns return `403` not `404`; admin overrides; rate limiter trips at the configured threshold |

Run via `pytest backend/tests -q`. Use `httpx.AsyncClient` against the FastAPI app and an in-memory or test-database fixture.

### O.2 Frontend — Playwright

| Flow | Purpose |
|---|---|
| **Login flow** | Login form rejects bad creds, accepts good ones, stores JWT, redirects to dashboard |
| **Upload flow** | Drag-and-drop a fixture image, start analysis, wait for completion, see the result page |
| **Result visibility** | Switch tabs (overlay/mask/density/morphology), values render correctly |
| **History search/filter** | Filter by project, status, date; pagination works |
| **Export flow** | Trigger CSV/PNG/PDF export; downloaded file has the expected size and content type |
| **Dashboard visual regression** | Screenshot test for the dashboard at common breakpoints |
| **Result page visual regression** | Screenshot test for the result page at common breakpoints |

**Why Playwright.** Real browser engines (Chromium, WebKit, Firefox), built-in waiting and auto-retry, network interception, video recording for failures, and screenshot diffing for visual regression. It is the right tool because Deeply Analytics is a UI-rich application; unit tests on components miss the issues that matter (auth flow, upload, file rendering).

**Status:** **[Proposed]** — no tests exist today.

---

## P. Deployment Plan

### P.1 Topology

```
                    ┌──────────────────────────┐
                    │  Browser (HTTPS)         │
                    └───────────┬──────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
       ┌──────▼──────┐                  ┌─────────▼──────────┐
       │  Vercel     │   API calls      │  Railway/Render/   │
       │  (frontend) │ ◄──────────────► │   VPS (FastAPI)    │
       └─────────────┘                  └─────────┬──────────┘
                                                  │
                              ┌───────────────────┼────────────────────┐
                              │                   │                    │
                       ┌──────▼──────┐    ┌───────▼─────────┐    ┌─────▼──────┐
                       │  Postgres   │    │  Object storage │    │  Worker(s) │
                       │ (managed)   │    │  (S3-compatible)│    │  (Celery)  │
                       └─────────────┘    └─────────────────┘    └────────────┘
```

### P.2 Environments

| Concern | Frontend | Backend |
|---|---|---|
| Host | Vercel | Railway / Render / VPS |
| Build | `npm run build` (Vite) | Docker image (`uvicorn`) |
| Env | `VITE_API_URL=https://api.deeply.app` | `DATABASE_URL`, `JWT_SECRET`, `STORAGE_BUCKET`, `STORAGE_KEY`, `STORAGE_SECRET`, `REDIS_URL`, `ALLOWED_ORIGINS` |
| Secrets | Stored in Vercel project | Stored in the host's secret manager |
| Logs | Vercel runtime logs | Host platform + structured JSON to a log sink |

### P.3 CORS

Backend allows exactly the production frontend origin and the staging origin:

```python
allow_origins=[
    "https://deeply.app",
    "https://staging.deeply.app",
    "http://127.0.0.1:5173",  # local dev only
]
```

No wildcard. No `allow_credentials=True` unless cookie-based auth is used.

### P.4 `VITE_API_URL`

The frontend reads `VITE_API_URL` at build time to point its `fetch` calls at the right backend. Local dev uses `http://127.0.0.1:8000`; staging and production point to their respective backends. The current MVP hard-codes `127.0.0.1:8000` in `frontend/src/api.ts` — this should be replaced by `import.meta.env.VITE_API_URL` before deployment.

### P.5 Separation of concerns

Frontend and backend deploy independently. A backend hotfix does not require a frontend rebuild and vice versa. The contract between them is the API spec in Section H; breaking changes go through versioned endpoints (`/api/v2/...`) rather than mutating existing ones.

**Status:** **[Proposed]** — local-only today.

---

## Q. Security Requirements

| Requirement | Detail | Status |
|---|---|---|
| **JWT auth** | HS256 or RS256 tokens; 60-minute access token + refresh token; signed with `JWT_SECRET` from env | [Proposed] |
| **Password hashing** | `argon2id` (or `bcrypt` with cost ≥ 12); never store plaintext | [Proposed] |
| **Protected frontend routes** | A `<RequireAuth>` wrapper redirects to `/login` when the JWT is missing or expired | [Proposed] |
| **Backend authorisation checks** | Services check `current_user` against resource ownership on every read/write; never trust the URL alone | [Proposed] |
| **Role-based access control** | Roles `user` and `admin`; admin endpoints behind a `require_role("admin")` dependency | [Proposed] |
| **Upload validation** | Content-type check, magic-byte sniffing on top of the extension, max size enforced by middleware | [Partial] — content-type and size limits exist in the MVP analysis service |
| **Rate limiting** | Per-user and per-IP buckets on `/auth/login`, `/analyses/upload`, `/reports/*`; e.g. 30 r/m per user | [Proposed] |
| **Secure environment variables** | All secrets read from env; never committed; rotated via the host's secret manager | [Proposed] |
| **No hardcoded secrets** | CI lint step rejects committed `.env` files and known-secret patterns | [Proposed] |
| **CORS allowlist** | Exact-origin allowlist; no `*`; no credentials unless explicitly required | [Implemented] — current MVP uses an exact allowlist |
| **HTTPS-only in production** | TLS terminated at the platform load balancer; HSTS header set | [Proposed] |

---

## R. Development Roadmap

The roadmap is split into two phases. Phase 1 brings the platform to a **persistent, multi-user MVP**. Phase 2 closes the gap to a production product.

### R.1 Phase 1 — Platform foundation

| # | Task | Deliverable | Depends on |
|---|---|---|---|
| 1 | Project setup | `backend/`, `frontend/`, `docker-compose.yml` for Postgres, env loading | — |
| 2 | DB models | SQLModel classes for `users`, `projects`, `analysis_jobs`; first Alembic migration | 1 |
| 3 | Auth | `/auth/register`, `/auth/login`, `/auth/me`; password hashing; JWT issuance and verification | 2 |
| 4 | Upload endpoint | `POST /analyses/upload` validated, persists to `storage/uploads/`, creates a `pending` job | 2, 3 |
| 5 | Analysis job table & status endpoint | `analysis_jobs` row with status; `GET /analyses/{id}/status` | 2, 4 |
| 6 | Simple dashboard UI | App shell (sidebar + header + outlet); protected routes; Dashboard page with last-N jobs; New Analysis page | 3, 4 |
| 7 | History list | History page with paginated table + basic filters | 5 |

### R.2 Phase 2 — Real product

| # | Task | Deliverable | Depends on |
|---|---|---|---|
| 8 | AI pipeline integration | Background worker (BackgroundTasks → Celery); `analysis_results` row written on completion; artefacts uploaded to object storage | Phase 1 |
| 9 | Result page | Tabs (overlay / mask / density / morphology); KPI tiles; status polling | 8 |
| 10 | Morphology + density outputs | Morphology rows persisted; density heatmap PNG generated and stored; result endpoints `morphology` and `density` | 8 |
| 11 | Export | CSV / PNG / PDF generation; download URLs; `exports` table | 9, 10 |
| 12 | Animation polish | Framer Motion variants for KPI grid, modal, result reveal; route cross-fade | 6, 9 |
| 13 | Playwright tests | Login, upload, result visibility, history filter, export, dashboard + result visual regression | 6, 9, 11 |
| 14 | Deployment | Vercel for frontend, Railway/Render/VPS for backend, managed Postgres, S3 storage, secret management, custom domain | All above |

---

## S. Quality Assessment

### S.1 What makes this project strong

- **A real, trained AI model** (`outputs/checkpoints/best_model.pth`) with verified outputs (counting, density, morphology) — not a wrapper around a pretrained API.
- **A working live MVP** today: upload → U-Net inference → mask + overlay + count → React UI rendering the result, all on the local machine.
- **Clear layered architecture** with one responsibility per layer; each layer is independently testable.
- **A persistent platform plan**: users, projects, jobs, results, exports — not a stateless demo.
- **Honest scope**: the spec marks each component as Implemented, Partial, or Proposed; there is no overclaiming.
- **Production-aware decisions**: background jobs, JWT, RBAC, rate limiting, object storage, deployment targets, monitoring metrics already specified in companion docs.
- **Specified contract**: REST endpoints, Pydantic schemas, and database tables are all defined before implementation.
- **Realistic UI/UX**: page list, components, animation strategy, palette, and state-management choices are concrete enough to build from.

### S.2 What makes this project look weak

- **Static screenshots dressed up as a product.** A "demo" with no persistence, no auth, and no history reads as a single notebook with a UI.
- **Overclaiming features that do not exist.** Saying "production-ready" while there is no DB, no auth, no deployment is the fastest way to lose credibility.
- **Animations everywhere.** Motion on every paragraph, icon, and table cell signals decoration, not engineering.
- **Heavy infrastructure too early.** Standing up Kubernetes, Kafka, or a vector DB before there is a working `pending → completed` flow is busywork.
- **A single 2000-line `main.py`** with routes, services, DB, and auth all in one file. Layered architecture is the cure.
- **Untyped responses.** Returning raw dicts from FastAPI handlers throws away the value of Pydantic and produces inconsistent JSON.
- **No background processing.** Synchronous inference inside the request handler will not survive any real load.
- **Hardcoded secrets, hardcoded URLs.** `JWT_SECRET = "changeme"` in source, or `fetch("http://127.0.0.1:8000/...")` in the production frontend, are immediate red flags.
- **No tests.** A platform with auth, file upload, and inference and zero pytest/Playwright coverage looks fragile regardless of how the UI looks.

---

## T. Final Recommendation

Build Deeply Analytics as a **two-phase web platform** rather than a single-shot demo. **Phase 1** turns the existing AI pipeline into a persistent, multi-user MVP: authentication, projects, an upload-to-result flow with a job table, and a simple dashboard with history. **Phase 2** adds the real product surface: background-worker inference, a tabbed result page with morphology and density, exports, animation polish via Framer Motion, Playwright coverage, and deployment to Vercel + Railway/Render with managed Postgres and object storage.

Anchor every step on three principles: **layered architecture** (thin routes, fat services, isolated AI module, isolated data access), **honest status tagging** (Implemented / Partial / Proposed), and **production-aware defaults** (JWT, RBAC, rate limiting, background jobs, object storage, env-driven config). Finished consistently, the result is a defensible AI platform — a software product with the AI inside — and not just an inference script with a web page in front of it.

---

*End of specification.*

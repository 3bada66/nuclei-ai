# Deeply Analytics — Animation & Integration Guide

> **Document type.** A practical, implementation-ready companion to `DEEPLY_ANALYTICS_FULL_SYSTEM_SPEC.md`. Two parts:
> - **Part 1 — Integration.** How each layer of the stack is wired and how a single analysis flows from a browser click to a rendered result.
> - **Part 2 — Animation.** How to design and build the website's motion system with Framer Motion, with copy-paste-ready recipes for every surface.
> **Status legend.** **[Implemented]** = verified in the repository today · **[Partial]** = exists in skeletal form · **[Proposed]** = part of the target architecture, not yet built.
> **Document version.** v0.1 — 2026-05-02.

---

# Part 1 — How everything works and is connected

## 1.1 Stack at a glance

| Layer | Technology | Role | Status |
|---|---|---|---|
| Browser UI | React 18 + Vite + TypeScript | Pages, components, state, motion | [Partial] |
| Bundler / dev server | Vite | Dev server (HMR) on `:5173`, production build to `dist/` | [Implemented] |
| HTTP client | `fetch` (today) → TanStack Query (proposed) | Talks to FastAPI; manages caching and polling | [Partial] / [Proposed] |
| Animation | Framer Motion | Page transitions, KPI reveal, modal, toast | [Proposed] |
| API | FastAPI on `:8000` | Routes, validation, auth, error handling | [Partial] |
| Validation | Pydantic v2 | Request/response models, field constraints | [Implemented] (response models) |
| Service layer | Plain Python classes/modules | Business rules, orchestration | [Partial] |
| Data access | SQLModel/SQLAlchemy + Alembic | Repositories, sessions, migrations | [Proposed] |
| Database | PostgreSQL 16 | Users, projects, jobs, results, exports | [Proposed] |
| AI module | PyTorch + segmentation_models_pytorch | U-Net inference, postprocessing, counting | [Implemented] |
| Background tasks | FastAPI BackgroundTasks → Celery | Async job execution | [Proposed] |
| Object storage | Local FS today, S3-compatible in prod | Images, masks, overlays, density, exports | [Partial] |
| Testing | pytest + Playwright | Backend unit/integration + frontend E2E | [Proposed] |
| Deployment | Vercel (frontend) + Railway/Render/VPS (backend) | Hosting | [Proposed] |
| Security | JWT, hashed passwords, RBAC, rate limiting | Access control | [Proposed] (CORS allowlist [Implemented]) |

## 1.2 The end-to-end picture

```
┌────────────────────────────────────────────────────────────────────┐
│ Browser                                                            │
│ ┌──────────────────────────────────────────────────────────────┐  │
│ │ React app (Vite)                                             │  │
│ │  Login → Dashboard → New Analysis → Result → History → Reports│ │
│ │  Framer Motion handles transitions, modal, KPI reveal        │  │
│ │  api/client.ts injects JWT, base URL = VITE_API_URL          │  │
│ └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬─────────────────────────────────┘
                                   │ HTTPS / JSON · Bearer JWT
                                   ▼
┌────────────────────────────────────────────────────────────────────┐
│ FastAPI app                                                        │
│ ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│ │ Routers         │  │ Pydantic schemas │  │ Auth dependency    │ │
│ │ auth, projects, │→ │ (validate in/out)│→ │ decode JWT, role   │ │
│ │ analyses, etc.  │  └──────────────────┘  └────────────────────┘ │
│ └────────┬────────┘                                                │
│          ▼                                                         │
│ ┌──────────────────────────────────────────────────────────────┐  │
│ │ Service layer (business rules)                               │  │
│ │   auth_service · project_service · analysis_service          │  │
│ │   result_service · export_service                            │  │
│ └──────┬─────────────────────────────────────┬─────────────────┘  │
│        ▼                                     ▼                    │
│ ┌──────────────────────┐         ┌──────────────────────┐         │
│ │ Repositories         │         │ AI inference layer   │         │
│ │ users, projects,     │         │ preprocess · infer · │         │
│ │ analyses, results,   │         │ postprocess · count ·│         │
│ │ morphology, exports  │         │ morphology · density │         │
│ └────────┬─────────────┘         └─────────┬────────────┘         │
│          ▼                                 ▼                       │
│ ┌──────────────────────┐         ┌──────────────────────┐         │
│ │ PostgreSQL (managed) │         │ Object storage (S3)  │         │
│ └──────────────────────┘         └──────────────────────┘         │
│                                                                    │
│ ┌──────────────────────────────────────────────────────────────┐  │
│ │ Background workers (Celery)                                  │  │
│ │   Pull job from queue → run pipeline → write results         │  │
│ └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## 1.3 The "click to result" walkthrough

This is the single most important sequence in the system. Each step shows the file, the contract, and the layer it lives in.

### Step A — User clicks "Run analysis" on `New Analysis` page

- **File:** `frontend/src/pages/NewAnalysis.tsx`
- **Action:** the page calls `analyses.upload(file, { project_id, threshold, min_area })` from `frontend/src/api/analyses.ts`.
- **HTTP:** `POST /analyses/upload` as `multipart/form-data`, `Authorization: Bearer <jwt>`.
- **Animation hook:** the upload card scales 1 → 1.01 on drag-over (CSS); the "Run analysis" button shows a spinner via Framer Motion (`AnimatePresence` swap of children).

### Step B — FastAPI receives the upload

- **File:** `backend/routers/analyses.py`
- **Validation:** Pydantic schema `AnalysisUpload` enforces `project_id: int`, `threshold: float ∈ [0,1]`, `min_area: int ≥ 0`, content-type starts with `image/`, body ≤ 25 MB (middleware).
- **Auth:** `Depends(current_user)` decodes the JWT and returns the `User`. If invalid → 401.
- **Authorisation:** the router calls `project_service.get_owned(project_id, current_user)` which raises 403 if the project does not belong to the user.

### Step C — Service creates a job and persists the upload

- **File:** `backend/services/analysis_service.py`
- **Action:** writes the bytes to `storage/uploads/{job_id}.{ext}` (local FS or S3 PUT), then inserts an `analysis_jobs` row with status `pending` via `repositories/analyses.py`.
- **Returns** to the router: `{job_id, status: "pending", project_id, created_at}`.
- **Router responds 202 Accepted** (the work has been queued, not done).

### Step D — Background worker picks up the job

- **File:** `backend/workers/tasks.py`
- **Trigger:** the service called `enqueue_analysis(job_id)` after persisting the job. Locally this is `BackgroundTasks.add_task(...)`; in production it is a Celery task pushed onto Redis.
- **Worker action:**
  1. Marks the job `processing`, sets `started_at`.
  2. Calls the AI module:
     ```
     rgb, tensor = preprocess(image_path, target_size=256)
     probs       = infer(tensor)                     # PyTorch U-Net
     mask        = postprocess(probs, threshold=...)
     count       = count(mask, min_area=...)
     morph       = morphology(mask)
     density_png = density(mask, image_shape=rgb.shape)
     ```
  3. Writes `mask.png`, `overlay.png`, `density.png` to `storage/results/{job_id}/`.
  4. Inserts an `analysis_results` row with `cell_count`, `processing_ms`, `mode`, paths.
  5. Bulk-inserts `morphology_records` rows.
  6. Marks job `completed`, sets `finished_at`. On exception, marks `failed` and stores `error_message`.

### Step E — Frontend polls until completion

- **File:** `frontend/src/hooks/useAnalysisJob.ts`
- **Behaviour:** uses TanStack Query `useQuery({ queryKey:["job", id], queryFn:..., refetchInterval: status === "completed" || status === "failed" ? false : 1500 })`.
- **HTTP:** `GET /analyses/{id}/status` returns `{job_id, status, progress?}`.
- **Animation:** while `status` is `pending`/`processing`, the workflow bar moves from *Upload* to *Segment* to *Count*; an indeterminate progress shimmer plays. When `status` flips to `completed`, the result tiles fade up sequentially.

### Step F — Result page renders

- **File:** `frontend/src/pages/AnalysisResult.tsx`
- **Calls:**
  - `GET /analyses/{id}` — summary
  - `GET /results/{id}/morphology` — per-nucleus rows + summary
  - `GET /results/{id}/density` — heatmap PNG (or signed URL)
- **Render:** Tabs `Overlay | Mask | Density | Morphology`. KPI tiles for `cell_count`, `processing_ms`, `mode`. Animation: cross-fade on tab switch (`AnimatePresence`), count number animated 0 → final via Framer Motion spring.

### Step G — User exports

- **File:** `frontend/src/pages/Reports.tsx`
- **Action:** clicks "Export PDF" → `POST /reports/{id}/export-pdf`.
- **Backend:** `export_service` checks the job is `completed` (else 409), renders the PDF, stores it in `storage/exports/{export_id}.pdf`, inserts an `exports` row, returns `{download_url}`.
- **UI:** success toast slides in; `AnimatePresence` controls auto-dismiss.

## 1.4 Boundary contracts

Each boundary in the stack has an explicit, typed contract. Get the contract right and the layers can change independently.

### Frontend ↔ API

- **Format:** JSON for everything except `POST /analyses/upload` (multipart).
- **Auth:** `Authorization: Bearer <jwt>` on every protected route.
- **Error shape:** `{ detail: string, code?: string }` so the UI can localise (`code: "image_too_large"`).
- **Date format:** ISO 8601 UTC (e.g. `2026-05-02T11:23:00Z`).
- **Pagination:** `?page=1&page_size=20`; response wraps payload in `{ items, total, page, page_size }`.

### API (router) ↔ Service

- **Direction:** routers call services; services never call routers.
- **Inputs:** routers pass already-validated Pydantic models and the `current_user`.
- **Outputs:** services return domain objects (dataclasses or Pydantic). Routers serialise via response models.
- **Errors:** services raise a small set of domain exceptions (`NotFound`, `Forbidden`, `Conflict`, `ValidationError`); a global FastAPI exception handler maps them to the right HTTP code.

### Service ↔ Repository

- **Direction:** services call repositories; repositories never call services.
- **Sessions:** the repository takes a SQLAlchemy session as a constructor argument; the service owns the session lifecycle.
- **Transactions:** one transaction per service method by default; explicit nested transactions only when needed.

### Service ↔ AI inference

- **Direction:** the worker (or service for sync MVP) calls AI module functions.
- **Contract:** pure functions. Input is bytes/ndarray/tensor; output is ndarray/dict; no side effects on the DB or HTTP.
- **Threading:** the model is a process-wide singleton, lazily initialised, protected by a module-level guard.

### Service ↔ Storage

- **Local dev:** `pathlib.Path` writes under `backend/storage/`.
- **Production:** an `ObjectStorage` interface with `put(key, bytes) -> url`, `get(key) -> bytes`, `presigned_url(key, ttl)`. S3-compatible backend (R2, Spaces, Backblaze, MinIO).
- **The DB stores keys, never bytes.**

## 1.5 Configuration map

Single source of truth: a `Settings` class loaded with `pydantic-settings`. Every secret and tunable is read from environment variables.

```python
# backend/config.py  [Proposed]
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = "dev"                                     # dev | staging | prod
    database_url: str
    jwt_secret: str
    jwt_alg: str = "HS256"
    jwt_ttl_seconds: int = 3600
    storage_root: str = "./backend/storage"              # local
    storage_bucket: str | None = None                    # S3
    storage_region: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    redis_url: str | None = None                         # Celery broker
    allowed_origins: list[str] = Field(default_factory=list)
    rate_limit_login_per_minute: int = 10
    rate_limit_upload_per_minute: int = 30
    max_upload_bytes: int = 25 * 1024 * 1024
    model_checkpoint: str = "outputs/checkpoints/best_model.pth"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

| Frontend env var | Used in | Purpose |
|---|---|---|
| `VITE_API_URL` | `frontend/src/api/client.ts` | Base URL of the backend (`http://127.0.0.1:8000` in dev) |
| `VITE_SENTRY_DSN` | `frontend/src/main.tsx` | (Optional) error reporting |

## 1.6 Where today's MVP plugs in

The current repository already implements the AI module, a FastAPI app, a single-page React UI, and a working synchronous pipeline. The integration plan above is the **target**; the table below shows where today's code sits inside it.

| Target component | Today's location | Notes |
|---|---|---|
| `backend/main.py` | `backend/main.py` | Has `/api/health`, `/api/analyze`, `/files/{name}` |
| `backend/services/analysis_service.py` | `backend/services/analysis_service.py` | Live U-Net wrapper; lazy singleton; fallback Otsu mode |
| `backend/schemas.py` | `backend/schemas.py` | `HealthResponse`, `AnalysisResponse`, `AnalysisMetadata` |
| AI inference layer | `src/infer.py`, `src/batch_count_refined.py`, `src/extract_morphology.py`, `src/generate_density_maps.py` | Imported by the service; not modified |
| Frontend single-page MVP | `frontend/src/App.tsx` + `components/{UploadPanel,ResultViewer,WorkflowSteps,MetricCard}.tsx` | Phase 1 expands this into the 7 official pages |
| Storage | `backend/storage/uploads/`, `backend/storage/results/` | Local FS; S3 in production |

---

# Part 2 — How to create the website's animations

## 2.1 What "good motion" means here

The dashboard is data-dense. Motion exists to **clarify state changes**, not to entertain. Three principles:

1. **Communicate, don't decorate.** Every animation is tied to a state change the user cares about: data arrived, modal opened, route changed, toast surfaced.
2. **Cheap, GPU-friendly properties only.** Animate `transform` and `opacity`. Avoid animating `width`, `height`, `top`, `left`, `box-shadow` (per-frame). For shadow changes, use CSS transitions on a static state, not Framer Motion.
3. **Respect the user.** Read `prefers-reduced-motion` and disable non-essential motion when the user has asked for it.

## 2.2 Why Framer Motion (and when to skip it)

| Use Framer Motion when… | Use plain CSS when… |
|---|---|
| You need enter/exit animations on conditional components (`AnimatePresence`) | You want a hover or focus effect on one element |
| You orchestrate sequenced reveals (KPI grid stagger) | You change colour or shadow on a single state |
| You drive transitions from React state | You only need a one-property transition |
| You want shared-layout transitions across routes | You target older browsers without bundle weight |

## 2.3 Installation and setup

```bash
cd frontend
npm install framer-motion
```

`package.json` (excerpt) [Proposed]:

```json
{
  "dependencies": {
    "framer-motion": "^11.5.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }
}
```

Wrap the app once for route-aware transitions:

```tsx
// frontend/src/App.tsx  [Proposed]
import { AnimatePresence } from "framer-motion";
import { useLocation } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import RoutesTree from "./routes";

export default function App() {
  const location = useLocation();
  return (
    <AppShell>
      <AnimatePresence mode="wait" initial={false}>
        <RoutesTree key={location.pathname} />
      </AnimatePresence>
    </AppShell>
  );
}
```

## 2.4 The shared variants library

One source of truth for motion. Lives in `frontend/src/lib/motion.ts`. Every component that animates pulls from this file so the system stays consistent.

```ts
// frontend/src/lib/motion.ts  [Proposed]
import type { Variants, Transition } from "framer-motion";

export const easeOut: Transition = { duration: 0.25, ease: [0.16, 1, 0.3, 1] };
export const easeQuick: Transition = { duration: 0.16, ease: "easeOut" };
export const spring: Transition = { type: "spring", stiffness: 240, damping: 28 };

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  show:   { opacity: 1, y: 0, transition: easeOut },
  exit:   { opacity: 0, y: -8, transition: easeQuick },
};

export const fade: Variants = {
  hidden: { opacity: 0 },
  show:   { opacity: 1, transition: easeOut },
  exit:   { opacity: 0, transition: easeQuick },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  show:   { opacity: 1, scale: 1, transition: easeOut },
  exit:   { opacity: 0, scale: 0.98, transition: easeQuick },
};

export const stagger = (gap = 0.04): Variants => ({
  hidden: { opacity: 1 },
  show:   { opacity: 1, transition: { staggerChildren: gap } },
});

export const slideInRight: Variants = {
  hidden: { x: "100%" },
  show:   { x: 0, transition: spring },
  exit:   { x: "100%", transition: easeQuick },
};
```

## 2.5 Per-surface animation recipes

Every recipe below is wired to a specific surface in the spec's 7 official pages.

### 2.5.1 Login page entrance

The form fades up; the brand mark precedes it by one beat.

```tsx
// frontend/src/pages/Login.tsx  [Proposed]
import { motion } from "framer-motion";
import { fadeUp, stagger } from "../lib/motion";

export default function Login() {
  return (
    <motion.section variants={stagger(0.06)} initial="hidden" animate="show" className="auth">
      <motion.h1 variants={fadeUp}>Deeply Analytics</motion.h1>
      <motion.p variants={fadeUp} className="muted">Sign in to continue</motion.p>
      <motion.form variants={fadeUp} onSubmit={onSubmit}>
        {/* email + password */}
      </motion.form>
    </motion.section>
  );
}
```

### 2.5.2 Sidebar slide-in on mobile

```tsx
// frontend/src/components/layout/Sidebar.tsx  [Proposed]
import { AnimatePresence, motion } from "framer-motion";
import { slideInRight } from "../../lib/motion";

export function MobileSidebar({ open, onClose, children }: Props) {
  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          className="sidebar-mobile"
          variants={slideInRight}
          initial="hidden"
          animate="show"
          exit="exit"
          aria-modal
          role="dialog"
        >
          <button onClick={onClose} aria-label="Close menu">×</button>
          {children}
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
```

### 2.5.3 KPI grid — staggered reveal

```tsx
// frontend/src/components/kpi/KpiGrid.tsx  [Proposed]
import { motion } from "framer-motion";
import { fadeUp, stagger } from "../../lib/motion";

export function KpiGrid({ kpis }: { kpis: { label: string; value: string }[] }) {
  return (
    <motion.div
      className="kpi-grid"
      variants={stagger(0.04)}
      initial="hidden"
      animate="show"
    >
      {kpis.map((k) => (
        <motion.div key={k.label} className="card" variants={fadeUp}>
          <h3>{k.label}</h3>
          <div className="metric-value">{k.value}</div>
        </motion.div>
      ))}
    </motion.div>
  );
}
```

Animate **only on first mount**, not on every refetch. With TanStack Query, gate animation by an `isFirstLoad` flag (`useRef(true)` cleared after first non-loading state).

### 2.5.4 Upload zone — drag feedback

CSS does most of the work; Framer Motion handles only the file-preview reveal.

```css
/* drag/hover handled in CSS — cheaper than motion */
.upload-zone { transition: transform 150ms ease-out, border-color 150ms ease-out; }
.upload-zone:hover { transform: translateY(-1px); }
.upload-zone.dragging { border-color: var(--primary); }
```

```tsx
// File-preview reveal
<AnimatePresence>
  {previewUrl && (
    <motion.img
      src={previewUrl}
      variants={fade}
      initial="hidden"
      animate="show"
      exit="exit"
    />
  )}
</AnimatePresence>
```

### 2.5.5 Workflow steps — active step pulse

Subtle: when `stage` advances, the new active step scales briefly.

```tsx
// frontend/src/components/workflow/WorkflowSteps.tsx  [Proposed]
import { motion } from "framer-motion";

const stepVariants = {
  inactive: { scale: 1 },
  active:   { scale: [1, 1.04, 1], transition: { duration: 0.45, ease: "easeOut" } },
  done:     { scale: 1 },
};

<motion.div
  className="workflow-step"
  variants={stepVariants}
  animate={state}            // "inactive" | "active" | "done"
>
  {step.label}
</motion.div>
```

### 2.5.6 Progress bar during analysis

Deterministic when the backend reports progress, indeterminate shimmer otherwise.

```tsx
// Determinate
<motion.div
  className="progress-fill"
  initial={false}
  animate={{ width: `${progress}%` }}
  transition={{ duration: 0.4, ease: "easeOut" }}
/>
```

```css
/* Indeterminate shimmer, CSS-only */
.progress-shimmer::before {
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  animation: shimmer 1.4s linear infinite;
}
@keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
```

### 2.5.7 Result reveal + animated count

When `status` flips to `completed`, the three image tiles fade up sequentially and the count tile counts from 0 to its final value.

```tsx
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect } from "react";

export function CellCount({ value }: { value: number }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (n) => Math.round(n).toLocaleString());

  useEffect(() => {
    const controls = animate(count, value, {
      duration: 0.9,
      ease: [0.16, 1, 0.3, 1],
    });
    return controls.stop;
  }, [value]);

  return <motion.span className="metric-value">{rounded}</motion.span>;
}
```

### 2.5.8 Result tabs — cross-fade with shared layout

```tsx
import { AnimatePresence, motion } from "framer-motion";
import { fade } from "../lib/motion";

export function ResultTabs({ active, panels }: Props) {
  return (
    <div className="tabs">
      <Header /* sets active */ />
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={active}
          variants={fade}
          initial="hidden"
          animate="show"
          exit="exit"
        >
          {panels[active]}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
```

For the underline that slides between tabs, use `layoutId`:

```tsx
{tabs.map((t) => (
  <button onClick={() => setActive(t)} key={t}>
    {t}
    {active === t && <motion.span layoutId="tab-underline" className="tab-underline" />}
  </button>
))}
```

### 2.5.9 Modal with `AnimatePresence`

```tsx
import { AnimatePresence, motion } from "framer-motion";
import { fade, scaleIn } from "../lib/motion";

export function Modal({ open, onClose, children }: ModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="modal-backdrop"
          variants={fade}
          initial="hidden"
          animate="show"
          exit="exit"
          onClick={onClose}
        >
          <motion.div
            className="modal-card"
            variants={scaleIn}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

Pair with focus trap and `Escape`-to-close — accessibility first; motion second.

### 2.5.10 Toasts

```tsx
import { AnimatePresence, motion } from "framer-motion";

export function Toast({ toast }: { toast: ToastType | null }) {
  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          className={`toast toast-${toast.tone}`}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 24 }}
          transition={{ duration: 0.18, ease: "easeOut" }}
        >
          {toast.message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### 2.5.11 Skeleton loaders

CSS-only is the right choice — these are background loops, not state-driven.

```css
.skeleton {
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 37%, #e2e8f0 63%);
  background-size: 400% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
  border-radius: 8px;
}
@keyframes skeleton-shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}
```

### 2.5.12 Route transitions

A short cross-fade between pages — never a slide that fights browser back navigation.

```tsx
// frontend/src/pages/_pageWrapper.tsx  [Proposed]
import { motion } from "framer-motion";
import { fade } from "../lib/motion";

export default function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <motion.main variants={fade} initial="hidden" animate="show" exit="exit">
      {children}
    </motion.main>
  );
}
```

Wrap each page's root element with `<PageWrapper>`.

## 2.6 Performance and accessibility

### 2.6.1 Respect `prefers-reduced-motion`

Use Framer Motion's built-in support:

```tsx
// frontend/src/main.tsx  [Proposed]
import { MotionConfig } from "framer-motion";

<MotionConfig reducedMotion="user">
  <App />
</MotionConfig>
```

This automatically disables non-essential motion for users with the OS setting on. For motion that **conveys meaning** (a progress bar), keep it on.

### 2.6.2 Animate the right properties

| Property | Cost | Verdict |
|---|---|---|
| `transform` (translate, scale, rotate) | GPU-accelerated | ✅ Use freely |
| `opacity` | GPU-accelerated | ✅ Use freely |
| `filter: blur()` | GPU-accelerated, but expensive | ⚠️ Use sparingly |
| `width`, `height`, `top`, `left` | Layout + paint per frame | ❌ Avoid |
| `box-shadow`, `border-radius` | Paint per frame | ❌ Use static states |

### 2.6.3 Avoid these mistakes

- Animating every paragraph or icon. Motion loses meaning when everything moves.
- Triggering animations on every data refetch. KPI grid animates on first mount only.
- Long durations (> 400 ms) for UI state changes. Aim for 150–250 ms.
- Heavy spring physics on small elements. Easing curves are calmer and more readable.
- Looping infinite particles in a data dashboard. Distracting and expensive.
- Animating layout (`width`/`height`). Animate `transform` or use `layout` prop with discipline.

## 2.7 Animation plan per page

| Page | What animates | What does not |
|---|---|---|
| **Login** | Form fade-up on mount; toast on error | Input focus (CSS only) |
| **Dashboard** | KPI stagger on first mount; recent-jobs table rows fade in once | Hover (CSS only) |
| **New Analysis** | Upload zone preview reveal; workflow step pulses on advance; progress bar | Drag-over (CSS) |
| **Analysis Result** | Tile sequential fade-up on completion; count counter; tab cross-fade; layoutId underline | Image hover (CSS) |
| **Analysis History** | First-mount row fade; filter panel slide-down on open | Sort indicator (CSS) |
| **Reports** | Export-success toast; download-list row fade | Format pills (CSS) |
| **Settings** | Tab cross-fade only | All else static |

## 2.8 Testing animations in Playwright

Animations slow tests and produce flaky screenshots. Two practical rules:

1. **Use `MotionConfig reducedMotion="always"` in test mode** by exposing a test flag (`window.__TEST__`) and reading it from `main.tsx`.
2. For visual-regression screenshots, wait for Framer Motion to settle:
   ```ts
   await page.locator(".kpi-grid").evaluate((el) =>
     Promise.all(el.getAnimations().map((a) => a.finished))
   );
   await expect(page).toHaveScreenshot();
   ```

---

# Part 3 — Stack details and recommendations

This part lists the concrete details the user asked about for each technology.

## 3.1 Frontend — React + Vite + TypeScript

**Why this stack.** React for the component model; Vite for fast HMR and zero-config TypeScript; TypeScript for typed contracts that line up with Pydantic on the backend.

**Key recommendations:**

- **Routing:** `react-router-dom` v6+; lazy-load each page with `React.lazy` to keep the initial bundle small.
- **Styling:** plain CSS variables + CSS modules. Avoid CSS-in-JS for a dashboard at this scale — slower runtime, harder to debug.
- **Forms:** `react-hook-form` for medium-complexity forms (Settings, New Analysis). Native HTML for Login.
- **HTTP:** central `api/client.ts` that injects the JWT and base URL. Never call `fetch` directly from a component.
- **Charts:** Recharts for simple analytics (morphology histograms); switch to ECharts or Visx if needs grow.
- **Icons:** `lucide-react` — consistent, tree-shakable.
- **Type generation:** generate frontend types from the FastAPI OpenAPI schema with `openapi-typescript`. Keeps the contract honest.

```ts
// frontend/src/api/client.ts  [Proposed]
const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("jwt");
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail ?? res.statusText, err.code);
  }
  return res.json();
}
```

## 3.2 Backend — FastAPI

**Why FastAPI.** Native async, automatic OpenAPI, Pydantic-first design.

**Key recommendations:**

- **Module split.** `routers/`, `schemas/`, `services/`, `db/`, `dependencies/`, `middleware/`. Never put SQL in routers.
- **Dependencies as the wiring point.** `Depends(current_user)`, `Depends(get_session)`, `Depends(require_role("admin"))`. They make tests trivial because they can be overridden.
- **Async only where it pays.** I/O routes (DB, HTTP) use `async def`. CPU-bound work (model inference) goes to a worker; do not run inference inside an event loop on the API process.
- **Errors.** A small `domain_exceptions.py` plus one global handler. Routers do not raise `HTTPException` directly except for input-shape failures.
- **OpenAPI.** Tag every router; document responses with `responses=` so the schema is self-explanatory.

## 3.3 Validation — Pydantic v2

**Key recommendations:**

- Define **separate schemas** for create / update / read. Never reuse the DB model as an HTTP schema.
- Use `Field(..., max_length=, ge=, le=)` for constraints; do not validate in the service if the schema can do it.
- For optional fields with defaults, use `Field(default=...)` not `Optional[...] = None` ambiguously.
- Configure `model_config = ConfigDict(extra="forbid")` on input schemas to reject typos.

## 3.4 Database — PostgreSQL + SQLModel/SQLAlchemy + Alembic

**PostgreSQL recommendations:**

- Version 15 or 16 in production; never SQLite for anything beyond unit tests.
- Use `JSONB` for the `analysis_jobs.parameters` column; index it only when needed.
- Foreign keys with `ON DELETE CASCADE` for derived data (`analysis_results`, `morphology_records`); `RESTRICT` for `users → projects` so accidental deletion does not orphan data.
- Indexes: `analysis_jobs(owner_id, created_at DESC)` for the history page; `analysis_jobs(status)` for the worker pull; `morphology_records(result_id)`.

**SQLModel vs SQLAlchemy:**

- **SQLModel** is faster to start: one class per table that doubles as a Pydantic schema. Best for teams that want minimal boilerplate.
- **SQLAlchemy 2.x** with explicit Pydantic schemas is more flexible long-term — better for teams that want a strict separation between DB models and HTTP schemas.

The spec is agnostic; pick one and stay with it.

**Alembic recommendations:**

- One migration per pull request that touches the schema; never edit a merged migration.
- Migration naming: `2026_05_15_add_morphology_records.py`.
- Run `alembic upgrade head` on backend boot in dev only; in prod run as a separate deploy step.
- Keep a `downgrade()` even if you rarely use it — having it forces you to think about reversibility.

## 3.5 AI module — PyTorch + segmentation_models_pytorch

**Recommendations:**

- **Lazy singleton.** Load the checkpoint once on first use, cache on a module global; this is already how `backend/services/analysis_service.py` works today.
- **Device handling.** `cuda` if available, `cpu` otherwise. The same code path runs on a CPU laptop and a GPU server.
- **Model versioning.** Store checkpoints under `outputs/checkpoints/v{N}/best_model.pth`; record the version in `analysis_results.model_version` so a result is reproducible.
- **Determinism.** Seed `torch.manual_seed(42)` and `np.random.seed(42)` at worker startup; record `torch.__version__` in metadata for traceability.
- **Quality gates.** As in `TECHNICAL_MONITORING_PLAN.md`: validation Dice and held-out count MAE compared to a baseline `D₀` and ≈277 respectively.
- **Keep `src/` pure.** The AI layer never imports from `backend/`. The dependency runs one way: `backend → src`.

## 3.6 Background tasks

**Recommendations:**

- **MVP:** FastAPI `BackgroundTasks`. Add the task inside the `POST /analyses/upload` handler **after** the DB row is persisted and the response is returned. This is enough for one-process local development.
- **Production:** Celery with a Redis broker. Two queues: `inference` (heavy, low concurrency) and `default` (light tasks like email/export). Worker autoscaling lives outside the API.
- **Job visibility:** every task writes status transitions to `analysis_jobs` (`pending → processing → completed | failed`). The `/api/health` and `/admin/queue` endpoints surface queue depth.
- **Retries:** Celery `autoretry_for=(TransientError,)` with exponential backoff and a max-retries cap.

## 3.7 Storage

**Recommendations:**

- **Abstraction.** A small `ObjectStorage` interface with `put`, `get`, `delete`, `presigned_url`. Two implementations: `LocalFsStorage` (dev) and `S3Storage` (prod, with `boto3`).
- **Keys, not paths.** Store `s3://deeply-prod/results/{job_id}/overlay.png` in the DB (or just the key), never `/Users/.../overlay.png`.
- **Lifecycle.** Bucket lifecycle policy auto-deletes uploads older than 30 days unless they have an associated completed result. Exports auto-delete after 14 days.
- **Public access:** **off**. Serve binaries through signed URLs that expire (e.g. 5 min); the `GET /results/{id}/overlay` endpoint mints them.

## 3.8 Testing — pytest + Playwright

**pytest:**

- Use `httpx.AsyncClient` against the FastAPI app via the `app.dependency_overrides` mechanism.
- Use a transactional fixture so each test rolls back: faster than `truncate`-per-test and impossible to leak.
- Factory pattern for fixtures (`user_factory`, `project_factory`).
- A small `client_as(user)` helper that returns an authenticated `AsyncClient`.

**Playwright:**

- One `tests/e2e/` directory in the frontend repo.
- Network-stubbed scenarios for upload-flow stability (`page.route(...)` to mock `/api/analyze`).
- Visual regression screenshots only on the dashboard and the result page; the rest are interaction tests.
- Run tests in CI with the FastAPI backend booted in a Docker compose service, against a seeded test DB.

## 3.9 Deployment

**Vercel (frontend):**

- Project root: `frontend/`.
- Build command: `npm run build`.
- Output directory: `dist`.
- Env: `VITE_API_URL` per environment (Preview, Production).

**Railway / Render / VPS (backend):**

- Containerise with a small Dockerfile (multi-stage, slim Python base, non-root user).
- Boot command: `uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- Worker as a separate service: `celery -A backend.workers.runner worker --loglevel=info`.
- Managed PostgreSQL: pick the platform's native option to avoid self-hosting.
- Redis: managed add-on.
- Object storage: any S3-compatible service.

**CORS:**

```python
allow_origins=[
    "https://deeply.app",
    "https://staging.deeply.app",
    "http://127.0.0.1:5173",
]
```

## 3.10 Security

**Minimum baseline:**

- **JWT** with HS256 (or RS256 if you split issuer); 60-minute access token plus a 30-day refresh token rotated on every use.
- **Password hashing** with `argon2id`; one secret per env (`JWT_SECRET`, `ARGON2_PEPPER`); never reuse.
- **Protected routes** on the frontend with a `<RequireAuth>` wrapper. The wrapper checks token presence + freshness; expired token → silent refresh, then redirect.
- **Backend authorisation** checks on every read/write — *never* trust the URL. The service compares `current_user.id` to the resource owner.
- **RBAC** as a `require_role("admin")` dependency. Only admins reach Settings → Admin and the user-management endpoints.
- **Upload validation** at three layers: middleware size limit, router content-type check, service magic-byte sniffing.
- **Rate limiting** on `/auth/login` (10/min/IP), `/analyses/upload` (30/min/user), `/reports/*` (60/min/user). Use `slowapi` for FastAPI.
- **Secrets** loaded from env, never committed. CI step (`detect-secrets`) blocks commits that contain known secret patterns.

---

# Part 4 — Implementation order checklist

A practical order of operations. Tick boxes as you build.

**Backend (in the order to write the code)**

- [ ] `backend/config.py` with `Settings`
- [ ] `backend/db/session.py` and first SQLModel for `users`
- [ ] First Alembic migration
- [ ] `backend/services/auth_service.py` (hash, verify, mint JWT)
- [ ] `backend/routers/auth.py` (`/register`, `/login`, `/me`)
- [ ] `backend/dependencies/auth.py` (`current_user`, `require_role`)
- [ ] Tables: `projects`, `analysis_jobs`, `analysis_results`, `morphology_records`, `exports`
- [ ] `backend/routers/projects.py`
- [ ] `backend/routers/analyses.py` with `upload`, `start`, `status`, `history`
- [ ] `backend/workers/tasks.py` and `BackgroundTasks` registration
- [ ] `backend/routers/results.py` (overlay, mask, density, morphology)
- [ ] `backend/services/export_service.py` and `routers/reports.py`
- [ ] CORS + rate limiter middleware
- [ ] pytest suite per router

**Frontend (in the order to ship)**

- [ ] App shell (sidebar + header + outlet) and routing tree
- [ ] `api/client.ts` with JWT injection and `VITE_API_URL`
- [ ] `AuthContext` + `RequireAuth`
- [ ] Login page + Login flow Playwright test
- [ ] Dashboard with KPI grid (skeletons → fadeUp on first load)
- [ ] New Analysis page (Upload + Workflow + Run)
- [ ] Job-status polling hook with TanStack Query
- [ ] Result page (Tabs + animated count + layoutId underline)
- [ ] History page with filters
- [ ] Reports page with export modal + toast
- [ ] Settings page
- [ ] `lib/motion.ts` shared variants and `MotionConfig reducedMotion="user"`
- [ ] Playwright E2E suite + visual regressions for Dashboard and Result

**Cutover to production**

- [ ] Add `VITE_API_URL` to Vercel project; remove hardcoded localhost
- [ ] Provision managed Postgres + Redis + S3 bucket
- [ ] Deploy backend image; run `alembic upgrade head` as part of release
- [ ] Configure CORS allowlist
- [ ] Wire `slowapi` rate limits
- [ ] Smoke-test login → upload → result on staging
- [ ] Promote to production

---

*End of guide. Pair this document with `DEEPLY_ANALYTICS_FULL_SYSTEM_SPEC.md` for the architectural overview.*
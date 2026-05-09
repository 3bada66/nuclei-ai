# Project Report — Draft

**AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting**

> Status legend used throughout this report: **[Implemented]** = verified in the current repository · **[Partial]** = exists in a prototype form · **[Proposed]** = part of the target academic architecture, not yet built.

---

## 1. Cover Page

| Field | Value |
|---|---|
| Project title | AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting |
| Course | Software Project Management & Technical Monitoring |
| Course code | _[to be filled]_ |
| Instructor | _[to be filled]_ |
| Semester / Academic year | _[to be filled]_ |
| Submission date | _[to be filled]_ |
| Team size | 4 members — **approved by the instructor** (course rule: 6–8; approval record in `INSTRUCTOR_APPROVAL_MESSAGE.md`, residual risk tracked in Section 15) |

**Team members and assigned roles**

| # | Name | Student ID | Role | Exact responsibilities |
|---|---|---|---|---|
| M1 | _[name]_ | _[id]_ | Project Manager + Risk Manager | Schedule, milestones, monitoring dashboards, risk register, stakeholder communication, instructor liaison |
| M2 | _[name]_ | _[id]_ | Lead Developer + Backend/API Lead | System architecture, FastAPI service, Pydantic schemas, SQLModel persistence, deployment to Railway |
| M3 | _[name]_ | _[id]_ | AI/ML Engineer + Data Processing Lead | U-Net training and inference, preprocessing, postprocessing, counting pipeline, model evaluation |
| M4 | _[name]_ | _[id]_ | UX/UI Designer + QA/Testing Lead | React+Vite+TS dashboard, 3D-inspired design system, pytest + Playwright suites, visual validation |

> A full breakdown of responsibilities, report contributions, presentation contributions, and monitoring duties is provided in `ROLE_ASSIGNMENT.md`.

---

## 2. Executive Summary

The AI-Powered Microscopy Analysis System is a web-based platform that helps biomedical researchers analyse microscopy images of cell nuclei. A user uploads a microscopy image; the system runs a U-Net deep learning model to segment the nuclei, applies post-processing, counts the cells, extracts morphological features, and returns visual outputs (overlays, masks, density heatmaps) together with a quantitative report.

The project is useful because manual nuclei counting is slow, subjective, and difficult to scale. By replacing the manual step with an AI pipeline, the system delivers consistent, repeatable measurements and frees researchers to focus on interpretation. From the perspective of this course, the project is also a vehicle to apply software project management and technical monitoring practices: progress is tracked through a management monitoring plan, and runtime behaviour is observed through a technical monitoring plan that watches API latency, inference duration, error rate, queue length, model availability, and uptime.

The current repository contains a working AI core — U-Net training, inference, counting, density-map generation, morphology extraction, and a Streamlit prototype dashboard **[Implemented]**. The full SaaS-style web application (FastAPI backend, React+Vite+TypeScript frontend, PostgreSQL persistence, JWT authentication, deployment to Vercel and Railway) is the **[Proposed]** target architecture for the academic plan.

---

## 3. Project Scope

### 3.1 In-scope features

- Microscopy image upload and storage **[Proposed]**
- U-Net nuclei segmentation **[Implemented]**
- Connected-component cell counting **[Implemented]**
- Density heatmap generation **[Implemented]**
- Morphology feature extraction (area, circularity, eccentricity, etc.) **[Implemented]**
- Overlay and mask visualisation **[Implemented]**
- CSV / structured export of analysis results **[Implemented]**
- Web dashboard — login page **[Proposed]**
- Web dashboard — upload page **[Proposed]**
- Web dashboard — analysis job status page **[Proposed]**
- Web dashboard — results visualisation page **[Proposed]**
- Web dashboard — monitoring page **[Proposed]**
- Web dashboard — export / report page **[Proposed]**
- Background inference jobs so the API does not block on long analyses **[Proposed]**
- JWT authentication, role-based access, rate limiting **[Proposed]**
- Management and technical monitoring dashboards **[Proposed]**
- 3D-inspired design language for the dashboard **[Proposed]**

### 3.2 Out-of-scope features

- Real-time microscope hardware integration
- Diagnostic / clinical decision-making (the system is a research tool, not a medical device)
- 3D volumetric microscopy reconstruction (z-stack)
- Multi-tenant billing and subscription management
- A full 3D rendering engine; the "3D design" is a 3D-inspired visual language, not WebGL geometry

### 3.3 Main users

- Biomedical and histopathology researchers analysing nuclei in tissue sections
- Laboratory technicians performing routine cell counts
- Course instructor and academic evaluators reviewing the project
- The development team itself, using the monitoring dashboards

### 3.4 System objectives

1. Reduce time spent on manual nuclei counting.
2. Produce repeatable, operator-independent counts and morphology metrics.
3. Expose the AI pipeline through a usable web interface.
4. Make project progress and system health observable through monitoring.
5. Demonstrate sound software engineering practice (layered architecture, validation, testing, deployment).

---

## 4. Problem Statement

Nuclei counting on microscopy images is a foundational measurement in histopathology and cell biology, yet in practice it is still done by hand or with semi-automated tools that require heavy operator tuning. Three problems follow:

1. **Manual counting is slow.** Annotation typically takes several minutes per image, which does not scale to studies that produce hundreds or thousands of fields of view (Ronneberger et al., 2015; Caicedo et al., 2019).
2. **Manual analysis is inconsistent.** Counts vary between observers and even between sessions of the same observer, which weakens downstream statistics.
3. **Researchers need faster and more reliable results** to iterate on experiments and meet publication timelines.

> **Acknowledged accuracy limit.** The current connected-component counter under-counts in regions of dense, touching nuclei. On the held-out evaluation set (37 images, XML ground truth), mean absolute error is approximately 277 cells per image. This limit is reflected in Section 5, in the technical monitoring quality gates (Section 12), and in risk #2 of `RISK_MANAGEMENT_PLAN.md`.

A fourth problem is internal to this course: the project itself must be **monitored**. Without a deliberate management monitoring plan, schedule slip and uneven workload are likely; without a technical monitoring plan, runtime regressions in the AI pipeline (slow inference, segmentation failures, queue back-pressure) are invisible until they cause user-facing failures.

---

## 5. Proposed Software Solution

The proposed solution is a web-based AI microscopy analysis platform with four interacting parts:

1. **A React + Vite + TypeScript dashboard** **[Proposed]** that lets the researcher log in, upload an image, follow analysis progress, view results (overlay, mask, heatmap, count, morphology), and export a report.
2. **A FastAPI service** **[Proposed]** that exposes REST endpoints for authentication, upload, analysis, job status, and results retrieval, validated by Pydantic models.
3. **An AI processing layer** **[Implemented]** built around a PyTorch U-Net (ResNet18 encoder) that performs preprocessing, segmentation, thresholding, connected-component labelling, counting, and morphological feature extraction.
4. **A persistence and storage layer** **[Proposed]** in which PostgreSQL (via SQLModel + Alembic) stores structured metadata and references, while object/file storage holds the binary artefacts (input images, masks, overlays, heatmaps, exports).

Long-running AI inference is dispatched to a background job runner so HTTP requests return quickly and the UI can poll job status. Both the management side and the technical side of the project are visible through monitoring surfaces (Section 11 and Section 12).

The current pipeline performs binary semantic segmentation followed by connected-component labelling. Because connected-component labelling cannot separate touching nuclei, the system under-counts in dense regions. This is the dominant source of error in the present implementation and is addressed by Section 12 (model-quality gates) and risk #2 in `RISK_MANAGEMENT_PLAN.md`.

---

## 6. Technology Stack and Platform Selection

| Layer | Technology | Status | Selection rationale |
|---|---|---|---|
| Frontend framework | React + Vite + TypeScript | [Proposed] | Fast dev loop, typed components, mature ecosystem for SaaS dashboards |
| API framework | FastAPI | [Proposed] | First-class async, automatic OpenAPI, native Pydantic integration |
| Validation | Pydantic | [Proposed] | Schema enforcement on requests, responses, and config |
| Architecture pattern | Layered (route → service → data) | [Proposed] | Separation of concerns, testability, clear ownership |
| Database | PostgreSQL | [Proposed] | Relational integrity for users, jobs, and analysis records |
| ORM | SQLModel (over SQLAlchemy) | [Proposed] | One model class for both ORM and Pydantic validation |
| Migration | Alembic | [Proposed] | Version-controlled schema evolution |
| AI framework | PyTorch + segmentation_models_pytorch | [Implemented] | U-Net with ResNet18 encoder, Dice + BCE loss, validated checkpoint |
| Image / CV | OpenCV, scikit-image, PIL, NumPy | [Implemented] | Pre/postprocessing, connected components, morphology |
| Background jobs | Async task queue (e.g. Celery / RQ / FastAPI BackgroundTasks) | [Proposed] | Keeps API non-blocking during inference |
| Object/file storage | Local file system today; S3-compatible storage in production | [Partial] | The `outputs/` tree on the local file system is in active use as storage today (masks, overlays, density maps, morphology CSVs). "Partial" here means *file-on-disk works*; S3 has not been configured. |
| Testing — backend | pytest | [Proposed] | Unit and integration coverage |
| Testing — E2E | Playwright | [Proposed] | Browser-driven dashboard validation |
| Frontend deployment | Vercel | [Proposed] | Zero-config deploy for Vite/React |
| Backend deployment | Railway | [Proposed] | Simple PaaS for FastAPI + Postgres |
| Auth & security | JWT, RBAC, rate limiting, env-based secrets | [Proposed] | Standard SaaS security baseline |
| Prototype UI | Streamlit (`src/app.py`) | [Implemented] | Demoable interactive surface for the AI core today |

### 6.1 Current vs. target

The current code base implements the AI core and a Streamlit-based interactive prototype. The web stack (FastAPI, React, PostgreSQL, SQLModel, Alembic, JWT, Vercel, Railway, Playwright) is the **target** academic architecture and is described as *Proposed*.

---

## 7. Software Design and Analysis Principles

| Principle | How the design honours it |
|---|---|
| **Maintainability** | Layered architecture; each layer has a single concern, so future changes (e.g. swapping the segmentation model) stay local. |
| **Scalability** | Stateless API, background workers, and object storage are designed so that additional worker instances can be added without schema changes. **[Proposed]** |
| **Cohesion** | The implemented modules in `src/` (training, inference, counting, density, morphology) each expose a single capability; the planned service and route layers will follow the same rule. |
| **Separation of concerns** | Routes handle HTTP, services orchestrate workflow, the data access layer talks to Postgres, the AI layer is pure inference. |
| **Modularity** | The AI pipeline is a sequence of replaceable stages; the frontend is a tree of small components. |
| **Reliability** | Background-job retries, schema validation at the boundary, and a technical monitoring plan that surfaces failures early. |
| **Testability** | Pure functions in the AI core, dependency-injected services, pytest for backend, Playwright for the dashboard. |

---

## 8. Architecture Overview

The proposed architecture is layered. Each layer has a single responsibility and a well-defined interface to the next.

```
┌──────────────────────────────────────────────┐
│ Frontend layer  (React + Vite + TS) [Proposed]│
└──────────────────────────────────────────────┘
                  │  HTTPS (JSON + JWT)
┌──────────────────────────────────────────────┐
│ API route layer  (FastAPI routers) [Proposed]│
└──────────────────────────────────────────────┘
                  │  validated DTOs
┌──────────────────────────────────────────────┐
│ Service layer  (orchestration) [Proposed]    │
└──────────────────────────────────────────────┘
       │                       │
┌──────────────┐      ┌──────────────────────┐
│ AI processing│      │ Data access layer    │
│ [Implemented]│      │ (SQLModel) [Proposed]│
└──────────────┘      └──────────────────────┘
       │                       │
┌──────────────┐      ┌──────────────────────┐
│ Storage      │      │ Database (Postgres)  │
│ [Partial]    │      │ [Proposed]           │
└──────────────┘      └──────────────────────┘
                  │
┌──────────────────────────────────────────────┐
│ Monitoring layer (logs, metrics, dashboards) │
│ [Proposed]                                   │
└──────────────────────────────────────────────┘
```

- **Frontend layer.** Renders pages, talks to the API over HTTPS, holds JWT, surfaces 3D-inspired UI.
- **API route layer.** FastAPI routers per resource (auth, uploads, jobs, results, monitoring). Pydantic models guard inputs and outputs.
- **Service layer.** Orchestrates workflows: e.g. *receive image → persist metadata → enqueue inference → on completion, persist results → notify*.
- **AI processing layer.** PyTorch U-Net, OpenCV postprocessing, connected-component counting, density and morphology computations.
- **Data access layer.** SQLModel repositories that hide SQL detail from services.
- **Database layer.** PostgreSQL holds users, jobs, analysis records, audit metadata; Alembic migrations track schema.
- **Storage layer.** Object/file storage for images, masks, overlays, heatmaps, exports — the database holds references only.
- **Monitoring layer.** Application logs, structured events, and metric exporters that feed a monitoring dashboard.

---

## 9. Basic UI / Dashboard Design

The dashboard is described page-by-page. Visual language and 3D-inspired direction are detailed in `UI_3D_DESIGN_CONCEPT.md` and Section 10.

| Page | Purpose | Key elements |
|---|---|---|
| **Login page** | Authenticate the researcher | Email, password, error state, link to recovery; protected routes redirect here |
| **Image upload page** | Submit a microscopy image for analysis | Drag-and-drop area, file metadata preview, "Start analysis" call-to-action |
| **Analysis job status page** | Show progress while the AI runs | Job ID, queue position, stage indicator (preprocess → predict → postprocess → count), elapsed time |
| **Results visualisation page** | Show the analysis output | Side-by-side original vs. overlay, segmentation mask, density heatmap, count, morphology table |
| **Monitoring dashboard** | Operational visibility | Latency, error rate, queue length, recent failed jobs, model availability (Section 12) |
| **Export / report page** | Take results out of the system | CSV download, PDF report, links to stored artefacts |

A Streamlit prototype that already covers upload, segmentation, counting, density heatmap, and morphology lives at `src/app.py` **[Implemented]** and serves as the visual reference until the React dashboard is built.

---

## 10. 3D Design Concept

This subsection summarises the 3D-inspired direction. The full specification is in `UI_3D_DESIGN_CONCEPT.md`.

- **Direction.** A 3D-inspired interface design language built on glassmorphism, depth, layered panels, soft shadow hierarchies, and isometric illustrations. It is **not** a 3D rendering engine.
- **Why 3D was selected.** Microscopy results are inherently visual; depth cues help the user separate the original image, the overlay, the heatmap, and the quantitative metrics. The same visual hierarchy supports clearer communication in the report and the in-class presentation.
- **Pages that use 3D-inspired elements.** Landing/hero, login, upload, analysis status, results, monitoring (see `UI_3D_DESIGN_CONCEPT.md` for per-page treatment).
- **How 3D improves visual communication.** Floating result cards, an isometric workflow diagram of the AI pipeline, layered panels in the monitoring dashboard, a 3D-style hero illustration on the landing page, and depth-tinted segmentation tiles all give evaluators an immediate read of the system.
- **Conceptual or implemented.** **Proposed / conceptual** for this term. The recommended deliverable is a Figma mockup set plus a CSS direction (glassmorphism tokens, shadow scale, layout grid) ready to plug into the planned React dashboard.

---

## 11. Management Monitoring Plan

The full plan is in `MANAGEMENT_MONITORING_PLAN.md`. The headline metrics are:

- Task completion percentage, weekly milestone status, schedule variance
- Report completion progress, presentation preparation status
- Risk status, team workload distribution
- Submission readiness, video recording readiness

Each metric carries an owner (M1–M4), a tracking method, and a frequency. The Project Manager (M1) consolidates them in a weekly status report and raises any red items as risks.

---

## 12. Technical Monitoring Plan

The full plan is in `TECHNICAL_MONITORING_PLAN.md`. The runtime metrics are:

- API response latency, upload success rate
- Inference job duration, segmentation failure rate
- Background job queue length, error rate
- Storage usage, database health
- Model output availability, system uptime, authentication failure rate

Each metric carries a threshold and a monitoring method (application logs, structured metrics, scheduled health probes). The Backend/API Lead (M2) and the AI/ML Engineer (M3) co-own the runtime metrics; the QA Lead (M4) owns end-to-end smoke checks.

---

## 13. Value Creation Analysis

| Dimension | Value created |
|---|---|
| **Customer value** | Researchers get fast, repeatable nuclei counts and morphology features without manual tallying. |
| **Business value** | Lab throughput rises; a research group can process more images per dollar of analyst time. |
| **Functional value** | Single platform covers upload → analysis → visualisation → export, replacing a chain of ad-hoc scripts. |
| **Operational value** | Monitoring dashboards make project execution and system health observable, supporting the course's monitoring focus. |
| **Technical value** | Modular AI pipeline + layered backend make the system a reusable base for future microscopy tasks (other stains, other organs, other cell types). |

---

## 14. Stakeholder Management Plan

The full stakeholder map is in `STAKEHOLDER_MANAGEMENT_PLAN.md`. The seven groups are:

1. **Project team (M1–M4)** — owners and primary executors.
2. **Instructor** — academic evaluator and approver of the 4-member team configuration.
3. **Researchers / lab users** — primary end users.
4. **System administrator** — handles deployment and storage in production.
5. **AI developer** — owner of model accuracy and pipeline stability (M3).
6. **End users** — anyone running an analysis through the dashboard.
7. **University / academic evaluators** — review the report, presentation, and video.

---

## 15. Risk Management Framework

The full risk register is in `RISK_MANAGEMENT_PLAN.md`. The framework follows: **Identification → Assessment → Mitigation → Monitoring → Ownership.** The eleven tracked risks include:

1. **Team has only 4 members instead of 6–8** *(compliance item — **resolved**: the instructor approved the 4-member team in writing; roles are consolidated across four members; residual risk is Low and limited to workload distribution).*
2. AI model may not perform accurately enough on dense regions.
3. Dataset preprocessing may take longer than expected.
4. Backend inference may be slow.
5. UI dashboard may remain too basic.
6. 3D design may stay conceptual and not visualise clearly.
7. Integration between frontend, backend, AI module, database, and storage may fail.
8. Schedule overrun.
9. Technical debt.
10. Presentation exceeding 7 minutes.
11. Video link permission problem.

The 4-member compliance risk is the headline item and is paired with a written request to the instructor (`INSTRUCTOR_APPROVAL_MESSAGE.md`).

---

## 16. Conclusion

The AI-Powered Microscopy Analysis System fits the *Software Project Management & Technical Monitoring* course on three counts. First, it has a working software product behind it — a U-Net segmentation pipeline with counting, density heatmaps, and morphology extraction. Second, it carries a realistic target web architecture (FastAPI, React+Vite+TS, PostgreSQL, SQLModel, JWT, Vercel, Railway) that exercises layered design, validation, testing, and deployment. Third, and most importantly for this course, it is wrapped in an explicit management monitoring plan, a technical monitoring plan, a risk register, a stakeholder map, a 4-person role assignment, a 7-minute presentation script, a 3D-inspired design concept, and a final submission checklist. Together, these artefacts demonstrate that the team can plan, build, observe, and deliver a software project under academic time constraints.

---

## 17. References

1. Ronneberger, O., Fischer, P., & Brox, T. (2015). *U-Net: Convolutional Networks for Biomedical Image Segmentation.* In *Medical Image Computing and Computer-Assisted Intervention (MICCAI)*, pp. 234–241.
2. Caicedo, J. C., Roth, J., Goodman, A., Becker, T., Karhohs, K. W., Broisin, M., Csaba, M., McQuin, C., Singh, S., Theis, F. J., & Carpenter, A. E. (2019). *Evaluation of Deep Learning Strategies for Nucleus Segmentation in Fluorescence Images.* *Cytometry Part A*, 95(9), 952–965.
3. Iakubovskii, P. (2019). *Segmentation Models PyTorch.* GitHub repository. https://github.com/qubvel/segmentation_models.pytorch
4. Paszke, A., Gross, S., Massa, F., et al. (2019). *PyTorch: An Imperative Style, High-Performance Deep Learning Library.* In *Advances in Neural Information Processing Systems*, 32.
5. Bradski, G. (2000). *The OpenCV Library.* *Dr. Dobb's Journal of Software Tools.*
6. van der Walt, S., Schönberger, J. L., Nunez-Iglesias, J., et al. (2014). *scikit-image: Image Processing in Python.* *PeerJ*, 2, e453.
7. Tiangolo, S. R. (2018–). *FastAPI Documentation.* https://fastapi.tiangolo.com/
8. Colvin, S. (2017–). *Pydantic Documentation.* https://docs.pydantic.dev/
9. Tiangolo, S. R. (2021–). *SQLModel Documentation.* https://sqlmodel.tiangolo.com/
10. Bayer, M. (2010–). *Alembic Documentation.* https://alembic.sqlalchemy.org/

---

*Document version: v0.2 — 2026-05-01*

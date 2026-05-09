# Role Assignment — 4-Member Team

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Team size:** 4 members — **approved by the instructor** (course rule: 6–8; approval record in `INSTRUCTOR_APPROVAL_MESSAGE.md`)

## Note on the 6–8 → 4 collapse

The official course announcement requires teams of 6–8 students. Our team has 4, and **the instructor has approved this configuration in writing** (see `INSTRUCTOR_APPROVAL_MESSAGE.md` for the approval record). To remain accountable to the rubric we have **consolidated** the roles a 6–8 team would distribute (Project Manager, Risk Manager, Backend Developer, Frontend Developer, AI/ML Engineer, Data Engineer, UX/UI Designer, QA/Test Engineer) into **four combined roles**. Each member therefore owns two adjacent responsibilities. The combined-role structure below is the version that was approved.

---

## Member 1 — Project Manager + Risk Manager

| | |
|---|---|
| **Role title** | Project Manager + Risk Manager |
| **Combined from** | Project Manager · Risk Manager · Documentation Lead |
| **Exact responsibilities** | Owns the schedule and milestone plan; runs weekly status meetings; maintains the management monitoring dashboard; keeps the risk register current; handles all communication with the instructor (including the approval message); chairs the submission checklist review; co-edits the report. |
| **Report contribution** | Sections 1 (Cover), 3 (Scope), 11 (Management Monitoring), 14 (Stakeholders), 15 (Risk), 16 (Conclusion). |
| **Presentation contribution** | Hook, problem framing, management monitoring slide, risk slide, closing message. Assigned as MC for the 7-minute talk. |
| **Monitoring responsibility** | All 9 metrics in `MANAGEMENT_MONITORING_PLAN.md`; raises any red item to the team within one working day. |

## Member 2 — Lead Developer + Backend/API Lead

| | |
|---|---|
| **Role title** | Lead Developer + Backend/API Lead |
| **Combined from** | Lead Developer · Backend Engineer · DevOps / Deployment Engineer |
| **Exact responsibilities** | Owns the FastAPI service and Pydantic schemas; designs the layered architecture (route → service → data); models persistence with SQLModel; runs Alembic migrations; integrates background job processing; deploys backend to Railway; coordinates with M3 to wrap the AI pipeline behind the service layer. |
| **Report contribution** | Sections 5 (Solution), 6 (Tech Stack), 7 (Design Principles), 8 (Architecture). |
| **Presentation contribution** | Architecture and tech-stack slide, system workflow walkthrough. |
| **Monitoring responsibility** | API latency, upload success rate, error rate, queue length, storage usage, database health, system uptime, authentication failure rate (see `TECHNICAL_MONITORING_PLAN.md`). |

## Member 3 — AI/ML Engineer + Data Processing Lead

| | |
|---|---|
| **Role title** | AI/ML Engineer + Data Processing Lead |
| **Combined from** | AI/ML Engineer · Data Engineer · Research Lead |
| **Exact responsibilities** | Owns the U-Net training pipeline, inference, thresholding, connected-component postprocessing, cell counting, density heatmaps, and morphology extraction. Maintains the trained checkpoint and evaluation metrics. Tunes hyperparameters (`tune_min_area.py`, `tune_threshold_xmlgt.py`). Documents model behaviour and known limits (e.g. under-counting in dense regions). |
| **Report contribution** | Sections 4 (Problem), 5 (Solution — AI portion), 8 (AI processing layer), 13 (Value Creation — technical/functional), 15 (Risk — model accuracy items). |
| **Presentation contribution** | AI pipeline slide, demo of segmentation/counting outputs, technical monitoring (model side). |
| **Monitoring responsibility** | Inference job duration, segmentation failure rate, model output availability (see `TECHNICAL_MONITORING_PLAN.md`). |

## Member 4 — UX/UI Designer + QA/Testing Lead

| | |
|---|---|
| **Role title** | UX/UI Designer + QA/Testing Lead |
| **Combined from** | UX/UI Designer · Frontend Engineer · QA / Test Engineer |
| **Exact responsibilities** | Owns the React + Vite + TypeScript dashboard; designs the 3D-inspired visual language (glassmorphism, depth, layered panels, isometric workflow illustration, hero illustration); builds the Figma mockup set; writes pytest backend cases (in coordination with M2) and Playwright end-to-end tests; runs visual regression checks; deploys the frontend to Vercel; records the backup video. |
| **Report contribution** | Sections 9 (UI), 10 (3D Design Concept), 13 (Value Creation — customer/operational), and the entire `UI_3D_DESIGN_CONCEPT.md` file. |
| **Presentation contribution** | 3D design concept slide, dashboard walkthrough, value-creation slide. |
| **Monitoring responsibility** | End-to-end smoke checks, Playwright run health, visual regression status; co-monitors upload success rate with M2. |

---

## Cross-cutting agreements

- One member is **never** the sole source of truth for any deliverable. Each artefact has an owner and a reviewer.
- The Project Manager (M1) chairs the weekly sync; minutes are stored alongside this `docs/` folder.
- All four members rehearse the 7-minute presentation together at least twice before submission (see `PRESENTATION_PLAN_7_MIN.md`).
- All four members sign off on the `FINAL_SUBMISSION_CHECKLIST.md` before submission.

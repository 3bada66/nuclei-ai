# Stakeholder Management Plan

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Owner:** M1 — Project Manager + Risk Manager

## Executive summary

This plan maps the seven stakeholder groups around the project — the team itself, the instructor, lab researchers, the system administrator, the AI developer, end users, and academic evaluators — and defines for each their interest, primary concern, communication channel, frequency, and the information they require. A RACI matrix consolidates accountability across the major artefacts (report, architecture, AI pipeline, frontend, monitoring plans, risk register, presentation, video, submission checklist), and a short set of communication norms governs day-to-day interaction. The plan is the relational counterpart to `MANAGEMENT_MONITORING_PLAN.md` and `RISK_MANAGEMENT_PLAN.md`.

## Purpose

This plan identifies the people and groups who care about, contribute to, or evaluate the project, and defines how the team communicates with each of them. The list intentionally separates the **academic** stakeholders (instructor, evaluators) from the **product** stakeholders (researchers, system administrator, end users) because each side asks different questions.

## Stakeholder map

| # | Stakeholder | Interest | Concern | Communication method | Communication frequency | Information needed |
|---|---|---|---|---|---|---|
| 1 | **Project team (M1–M4)** | Deliver a working, well-monitored project that earns a strong grade and a usable AI tool | Workload across only 4 members; integration risk between frontend, backend, AI, DB, storage | Weekly team sync; team channel; shared `docs/` folder | Weekly sync; daily async messages | Status of monitoring metrics; open risks; open tasks; submission checklist state |
| 2 | **Instructor** | Verify that the project meets the *Software Project Management & Technical Monitoring* rubric | Team size compliance (4 vs. 6–8); rigour of monitoring; quality of report and presentation | Email / official course channel; in-class presentation; written approval message (`INSTRUCTOR_APPROVAL_MESSAGE.md`) | Once for approval; once for any scope change; final submission and presentation | Approval of 4-member team; clear monitoring plans; well-formed report; on-time submission |
| 3 | **Researchers / lab users** | Get fast, repeatable nuclei counts and morphology features from microscopy images | Whether AI counts are trustworthy in dense regions; how to interpret outputs | Demo session; written user guide (informal during the course) | Once during demo; on request | What the system does well, what it does poorly, how to read overlays / heatmaps / counts |
| 4 | **System administrator** | Keep the deployed system reachable and within resource budgets | Storage growth, deployment process, backups, secrets handling | Operational runbook; the Monitoring Dashboard; deployment notes | On deploy; weekly health summary | Deployment steps; environment variables; backup/restore procedure; storage and DB usage |
| 5 | **AI developer (M3)** | Maintain and improve model accuracy and pipeline stability | Training data quality, evaluation metrics, model drift, dense-region under-counting | Code reviews; weekly sync; AI section of the report | Continuous during development; weekly summary | Latest evaluation metrics; failure cases; checkpoint version; threshold and `min_area` settings |
| 6 | **End users** | Run an analysis through the dashboard and get a result they can export | Onboarding friction, response time, clarity of results | Dashboard UX; in-app tooltips and empty states; export view | Per session | How to upload, where the job is, what the numbers mean, where to download |
| 7 | **University / academic evaluators** | Assess the project as a complete academic deliverable | Completeness, originality, evidence of monitoring, quality of presentation | Final report PDF; in-class presentation; backup video link | At final submission | Report, slides, video link with verified access, monitoring tables, risk register |

## RACI summary (per major artefact)

| Artefact | M1 | M2 | M3 | M4 |
|---|---|---|---|---|
| Project report | **R/A** | C | C | C |
| Architecture & backend | I | **R/A** | C | C |
| AI pipeline | I | C | **R/A** | I |
| Frontend dashboard & 3D design | I | C | I | **R/A** |
| Monitoring plans | **R/A** | C | C | C |
| Risk register | **R/A** | I | I | I |
| Presentation slides | C | C | C | **R/A** |
| Backup video | C | I | I | **R/A** |
| Submission checklist | **R/A** | C | C | C |

(R = Responsible, A = Accountable, C = Consulted, I = Informed.)

## Communication norms

- **Default channel.** Team chat for async; weekly sync for decisions; `docs/` for anything that has to survive the conversation.
- **Instructor.** Email / official course channel only. Never DM. M1 is the single point of contact.
- **Decisions.** Recorded as a one-line entry in the weekly status report.
- **Bad news first.** Whoever sees a 🟡 or 🔴 raises it the same day; severity is set by the team, not by the spotter.

---

*Document version: v0.2 — 2026-05-01*

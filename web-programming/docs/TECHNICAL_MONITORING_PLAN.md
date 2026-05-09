# Technical Monitoring Plan

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Co-owners:** M2 (Backend/API), M3 (AI/ML), with M4 contributing end-to-end smoke checks

## Executive summary

This plan establishes how the team observes the running system. Eleven runtime metrics cover availability, latency, throughput, errors, storage, and authentication. Two model-quality gates — validation Dice and held-out count MAE — are pinned to the verified baseline produced by the current trained checkpoint, so model regressions are detectable rather than implicit. Thresholds, monitoring methods, and an escalation protocol are defined; the canary inference job and the scheduled Playwright smoke run together provide a pragmatic minimum bar for "the system is alive and the model still segments." The plan is the technical counterpart to `MANAGEMENT_MONITORING_PLAN.md`.

## Purpose

This plan defines how the team observes the **running system**. It is the counterpart to `MANAGEMENT_MONITORING_PLAN.md`, which monitors project execution. The metrics below are collected from application logs, structured event streams, scheduled health probes, and end-to-end smoke runs.

> Status note: in the current repository the AI core is **[Implemented]** but the FastAPI service, async queue, and PostgreSQL layer are **[Proposed]**. The thresholds below describe the operating envelope for the proposed system; they are also useful targets for the prototype.

## Monitoring metrics

| # | Metric | What it measures | Why it matters | Example threshold | Monitoring method |
|---|---|---|---|---|---|
| 1 | **API response latency** | p50 and p95 response time of FastAPI endpoints | Slow APIs degrade UX and can mask deeper failures | p95 < 500 ms for non-inference endpoints | Application middleware logs request duration; aggregated per endpoint |
| 2 | **Upload success rate** | Share of image uploads that complete without error | Uploads are the entry point — a failed upload blocks the whole workflow | ≥ 99 % over a rolling 24 h window | Service-layer counters on upload endpoint; alert on drop |
| 3 | **Inference job duration** | Wall-clock time from "predict start" to "predict end" per image | Long inference jobs starve the queue and frustrate users | p95 < 30 s on a standard image size | Timestamps emitted by the AI processing layer; histogram per day |
| 4 | **Segmentation failure rate** | Share of jobs that error or yield empty/degenerate masks | Direct quality signal for the core capability | < 1 % per week | Postprocessing checks (mask area, count plausibility); failures logged with input metadata |
| 5 | **Background job queue length** | Number of pending inference jobs in the queue | Queue growth signals back-pressure or a stuck worker | < 5 sustained for > 5 min | Queue inspection probe; structured metric |
| 6 | **Error rate** | 5xx responses + uncaught service exceptions per hour | Fast feedback that something is broken | < 0.5 % of requests | API middleware error counters; structured log search |
| 7 | **Storage usage** | Used capacity in object/file storage | Microscopy images and masks are large; running out of space halts the system | Alert at 80 % of allocated quota | Periodic probe of storage backend |
| 8 | **Database health** | Postgres up/down, connection count, replication / migration state | Database loss = total loss of metadata | All probes pass; connection count < 80 % of max | Health endpoint + DB-side metric exporter |
| 9 | **Model output availability** | Whether the trained checkpoint loads and produces a non-empty mask on a canary image | Detects model file corruption or environment drift | 100 % on every cold start; nightly canary | Scheduled canary inference job; alert on failure |
| 10 | **System uptime** | Share of minutes the API responds healthily | Headline reliability number | ≥ 99 % monthly | External / scheduled health probe |
| 11 | **Authentication failure rate** | Failed login attempts per minute | Sudden spikes indicate brute-force or a regression in the auth flow | Alert on > 10/min from a single client | Auth middleware logs |

### Model-quality gates (anchored to verified baseline)

The two gates below treat the current trained checkpoint as the baseline and detect regressions whenever the model is retrained or the postprocessing changes. The baseline values are the verified results produced by the model artefacts already on disk (`outputs/checkpoints/best_model.pth` and the held-out evaluation in `outputs/counting_batch_refined_xmlgt/count_results.csv`).

| # | Quality gate | Baseline (verified, current checkpoint) | 🟢 Acceptable | 🟡 Investigate | 🔴 Block release | Monitoring method |
|---|---|---|---|---|---|---|
| Q1 | **Validation Dice score** (binary segmentation) | _baseline = `D₀`, computed from the validation split during training_ | ≥ `D₀ − 0.02` | drop of 0.02–0.05 vs. baseline | drop > 0.05 vs. baseline | Re-run `src/metrics.py` on the validation split after every training change |
| Q2 | **Held-out count MAE** (37 images, XML ground truth) | ≈ 277 cells / image (acknowledged limitation in dense regions) | ≤ 277 × 1.10 = ≤ 305 | 305–360 | > 360 | Re-run `src/batch_count_refined.py` on the held-out set; compare `count_results.csv` |

> Note. `D₀` is left symbolic in this document because the validation Dice value is recorded in the training run history rather than as a single number in the repo. The team records `D₀` next to this table the first time the plan is applied; subsequent runs are compared to it.

These two gates close the loop on **model quality** that runtime metric #4 (segmentation failure rate) only proxies. They are owned by M3 and reviewed any week the AI pipeline changes.

## Operating notes

- **Logging convention.** All services log JSON with `request_id`, `user_id` (if authenticated), `job_id` (if applicable), and `stage`. Stages used: `upload`, `preprocess`, `predict`, `postprocess`, `count`, `morphology`, `export`.
- **Canary inference.** A small reference microscopy image is run through the pipeline once per night. Output mask area and predicted count are checked against a stored expected range; deviation triggers an alert.
- **Smoke E2E.** Playwright is scheduled to run the full upload-to-result flow once per deployment and once per day; failure trips a 🔴 status.
- **Dashboards.** All metrics surface on the Monitoring Dashboard page of the React app (Section 9 of the report). The same data feeds an internal Grafana-style view for the team.

## Escalation

- 🟢 — All metrics inside thresholds. No action.
- 🟡 — Any one metric outside its threshold for ≤ 30 min. M2/M3 acknowledge in the team channel; investigate within the same day.
- 🔴 — Any one metric outside its threshold for > 30 min, or any "model output availability" failure, or any "database health" failure. Pause new feature work; M1 is informed; root cause is recorded in the risk register.

---

*Document version: v0.2 — 2026-05-01*

# Management Monitoring Plan

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Owner of this plan:** M1 — Project Manager + Risk Manager

## Executive summary

This plan establishes how the team observes the management dimensions of the project: schedule adherence, scope progress, workload balance, risk status, and submission readiness. Nine metrics are defined, each with a numeric Green/Amber/Red threshold, an owner, a tracking method, and a fixed cadence. The Project Manager consolidates the metrics in a weekly written status report (template and one worked example are included below). Workload distribution (metric #7) is the chief residual control associated with risk #1 in `RISK_MANAGEMENT_PLAN.md`, given that the team operates with 4 members under instructor approval rather than the 6–8 specified by the course.

## Purpose

This plan defines how the team monitors the **management side** of the project: schedule, scope, workload, risk status, and submission readiness. It is the counterpart to `TECHNICAL_MONITORING_PLAN.md`, which monitors the running system.

The Project Manager consolidates these metrics into a single weekly status report. Any metric flagged red is escalated to the team within one working day and, if it threatens the deadline, raised to the instructor.

## Definitions

- **Task completion percentage.** Effort-weighted: each task carries an estimated effort in hours (recorded on the project board). The percentage is the sum of completed-task hours divided by the sum of planned-task hours for the current phase. Count-weighted percentage is reported as a secondary number for quick reading.
- **Schedule variance (SV).** Computed per task as `actual_finish_date − planned_finish_date` in working days. The plan-level SV is the median across active tasks; the worst-case SV is also reported.
- **Workload distribution.** Self-reported hours per member per week. Imbalance is the spread `max − min` divided by the mean across the four members.

## Monitoring metrics

| # | Metric | Purpose | Owner | Tracking method | Frequency | 🟢 Green | 🟡 Amber | 🔴 Red |
|---|---|---|---|---|---|---|---|---|
| 1 | **Task completion percentage** | Show how much of the planned work is done | M1 | Project board (GitHub Projects / Trello), effort-weighted | Weekly | ≥ 90 % of weekly plan closed | 70–90 % | < 70 % |
| 2 | **Weekly milestone status** | Confirm each weekly milestone is met | M1 | Weekly status meeting; written summary appended to `docs/` | Weekly | Milestone met on planned date | Met within +2 working days | Slipped > 2 working days |
| 3 | **Schedule variance (SV)** | Detect schedule slip early | M1 | Gantt / timeline chart, working-day variance per task | Weekly | Median SV ≥ −2 days | −2 to −5 days | < −5 days |
| 4 | **Report completion progress** | Track completeness of the academic report (17 sections) | M1 (with section owners) | Section status in `PROJECT_REPORT_DRAFT.md` | Weekly | ≥ planned % per phase | within 10 pts of plan | > 10 pts behind plan |
| 5 | **Presentation preparation status** | Keep the 7-minute talk ready and on budget | M1, M4 | Slide draft state, rehearsal log, timed dry runs | Weekly in last 3 weeks; daily in final week | Slides drafted on plan; latest dry run ≤ 7:00 | Slides drafted; dry run 7:00–7:20 | Slides incomplete or dry run > 7:20 |
| 6 | **Risk status** | Track open vs. closed risks | M1 | `RISK_MANAGEMENT_PLAN.md` reviewed weekly | Weekly | 0 Critical, ≤ 1 High open | 0 Critical, 2–3 High | ≥ 1 Critical, or ≥ 4 High |
| 7 | **Team workload distribution** | Detect overload — the chief residual control for risk #1 (4-member team) | M1 | Self-reported hours per member | Weekly | Spread `(max − min) / mean` ≤ 0.20 | 0.20–0.40 | > 0.40 |
| 8 | **Submission readiness** | Confirm `FINAL_SUBMISSION_CHECKLIST.md` is on track | M1 (whole team signs off) | Checklist review | Weekly until 2 weeks before deadline; daily in final week | ≥ 90 % of checklist items ticked at the planned date | 70–90 % | < 70 % |
| 9 | **Video recording readiness** | Backup presentation video is recorded, uploaded, link-tested | M4 (lead), M1 (verifier) | Recording, upload, permission test from a logged-out account | Once 2 weeks out; then daily in final week | Recorded, uploaded, link verified ≥ 7 days before deadline | Recorded but link not verified | Not recorded with ≤ 3 days to deadline |

## Status report template (used weekly)

> **Week of `YYYY-MM-DD` — Overall status: 🟢 / 🟡 / 🔴**
>
> - Task completion (effort-weighted / count): … % / … %
> - Schedule variance (median / worst-case): … days / … days
> - Milestones met: … of …
> - Report completion: … of 17 sections final
> - Presentation latest dry-run time: …
> - Open risks: … Critical, … High, … Medium, … Low
> - Workload spread `(max − min) / mean`: …
> - Submission checklist progress: … %
> - Decisions needed from the instructor: …
> - Plan for next week: …

The report is appended to the `docs/` folder so it is part of the audit trail at submission.

## Worked example — Week of 2026-05-01

> **Week of 2026-05-01 — Overall status: 🟡**
>
> - Task completion (effort-weighted / count): 78 % / 82 %
> - Schedule variance (median / worst-case): −1 day / −4 days
> - Milestones met: 2 of 3 (UI mockup milestone slipped from 2026-04-28 to 2026-05-04)
> - Report completion: 12 of 17 sections final; Sections 9, 10, 12, 15, 17 still in draft
> - Presentation latest dry-run time: 7:18 (M4 to trim slide 9 bullets)
> - Open risks: 0 Critical, 2 High (#4 inference latency, #10 presentation overrun), 4 Medium, 3 Low
> - Workload spread `(max − min) / mean`: 0.27 (M3 carrying extra hours; rebalance moved one preprocessing task to M2)
> - Submission checklist progress: 64 %
> - Decisions needed from the instructor: none this week
> - Plan for next week: finalise Sections 9, 10, 12; second timed dry-run; freeze report skeleton

This example is illustrative; weekly entries during the live project replace it.

## Escalation rules

- 🟢 — On track. No action beyond the weekly report.
- 🟡 — At risk. M1 raises the issue in the next sync; the affected owner proposes a recovery plan within 2 working days.
- 🔴 — Off track. M1 calls an out-of-cycle meeting within 1 working day; the team reassesses scope and, if necessary, informs the instructor.

---

*Document version: v0.2 — 2026-05-01*

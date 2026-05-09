# Risk Management Plan

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Owner:** M1 — Project Manager + Risk Manager

## Executive summary

This document records eleven tracked risks across compliance, technical, schedule, quality, and submission categories. Each risk is rated on probability and impact, scored on a severity matrix, assigned a single owner, and linked to a monitoring method. The headline compliance item — operating with 4 members against a course rule of 6–8 — has been resolved by written instructor approval; the residual control is workload monitoring (metric #7 in `MANAGEMENT_MONITORING_PLAN.md`). The remaining risks of greatest weight are integration failure between the planned frontend, backend, AI, database, and storage layers (#7), schedule overrun (#8), presentation overrun (#10), and video link permission failure (#11).

## 1. Framework

The team applies a five-step framework to every risk:

1. **Risk identification.** Risks are surfaced in the weekly status meeting, by any team member at any time, or as a side effect of a 🟡/🔴 monitoring alert.
2. **Risk assessment.** Each risk is rated on probability (Low / Medium / High) and impact (Low / Medium / High); severity is the combined score (Low / Medium / High / Critical).
3. **Risk mitigation.** A specific, actionable mitigation is recorded — not a generic "be careful." Where possible, a contingency action is also recorded.
4. **Risk monitoring.** Each risk is re-checked weekly. Status changes (probability, impact, mitigation progress) are logged.
5. **Risk owner.** Exactly one team member owns each risk. The owner is responsible for the mitigation, not necessarily for executing it personally.

## 2. Severity matrix

|  | Low impact | Medium impact | High impact |
|---|---|---|---|
| **Low probability** | Low | Low | Medium |
| **Medium probability** | Low | Medium | High |
| **High probability** | Medium | High | Critical |

## 3. Risk register

| # | Risk | Type | Probability | Impact | Severity | Mitigation | Owner | Monitoring method |
|---|---|---|---|---|---|---|---|---|
| 1 | **Team has only 4 members instead of 6–8** | Compliance / organisational | Low | Medium | **Low** *(residual — see status note)* | **Status: Resolved.** Instructor approval received; roles are consolidated across four members (see `ROLE_ASSIGNMENT.md` and approval record in `INSTRUCTOR_APPROVAL_MESSAGE.md`). Residual mitigation: monitor workload distribution (management metric #7) so the smaller team does not overrun. | M1 | Workload check at the weekly sync; no further compliance action required |
| 2 | AI model may not perform accurately enough | Technical / quality | Medium | High | High | Use the existing trained U-Net checkpoint as a baseline; tune threshold and `min_area`; document known failure mode (under-counts in dense regions); add a manual-review path on the results page. | M3 | Segmentation failure rate + count MAE on the held-out set, weekly |
| 3 | Dataset preprocessing may take longer than expected | Schedule / data | Medium | Medium | Medium | Reuse existing splits in `data/`; cache preprocessed tensors; parallelise where simple. Contingency: reduce dataset size for the demo. | M3 | Schedule variance for preprocessing tasks |
| 4 | Backend inference may be slow | Performance | Medium | High | High | Run inference asynchronously via background jobs so the API stays responsive; pre-warm model at boot; consider batch inference for queued jobs. | M2, M3 | Inference job duration (technical metric #3); queue length (#5) |
| 5 | UI dashboard may remain too basic | Quality / scope | Medium | Medium | Medium | Lock the page list early (Section 9 of the report); reuse the Streamlit prototype layout as a reference; ship a minimum credible version of every page before polishing any one. | M4 | Weekly UI review at the team sync |
| 6 | 3D design may stay conceptual and not visualise clearly enough | Quality / presentation | Medium | Medium | Medium | Treat 3D as a **proposed design concept** (see `UI_3D_DESIGN_CONCEPT.md`); produce a Figma mockup set and a glassmorphism CSS tokens file; embed mockups in the report and slides. | M4 | Mockup completeness checked weekly |
| 7 | Integration between frontend, backend, AI module, database, and storage may fail | Technical / integration | Medium | High | High | Build vertical slice end-to-end early (login → upload → inference → result) before broadening scope; contract tests on Pydantic schemas; feature flag for partial integration. | M2 | E2E smoke (Playwright) per deployment + nightly |
| 8 | Schedule overrun | Schedule | Medium | High | High | Weekly milestone check; trim scope to the in-scope list (Section 3.1); freeze the report skeleton early so writing happens in parallel with development. | M1 | Schedule variance (management metric #3) |
| 9 | Technical debt | Quality | Medium | Medium | Medium | Layered architecture from day one; review PRs against architecture rules; do not skip Pydantic validation under deadline pressure. | M2 | PR review log; debt items tracked as tasks |
| 10 | Presentation exceeding 7 minutes | Compliance / presentation | High | Medium | High | Use the slide-by-slide table in `PRESENTATION_PLAN_7_MIN.md`; rehearse with a stopwatch at least twice; if a section runs long, cut bullets, not slides. | M1, M4 | Timed dry runs in the final 2 weeks |
| 11 | Video link permission problem | Compliance / submission | Medium | High | High | Upload the backup video at least 48 h before the deadline; test the link from a non-team account; verify that "Anyone with the link" / public-view permission is enabled. | M4, M1 | Permission-test step in `FINAL_SUBMISSION_CHECKLIST.md` |

## 4. Review cadence

- Weekly during the team sync — recompute severity, close resolved risks, register new ones.
- Daily in the final week before submission — only items #1, #5, #6, #10, #11 are checked.

## 5. Closing a risk

A risk is closed only when (a) the trigger condition has passed, (b) the mitigation is in place and verified, or (c) the risk has materialised and been documented as an issue with a recovery plan.

---

*Document version: v0.2 — 2026-05-01*

# Presentation Plan — 7 Minutes

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Total budget:** 420 seconds (7:00) — hard cap
**MC:** M1 · **Co-presenters:** M2, M3, M4

## Storytelling arc

> *Hook → Problem → Proposed solution → System workflow → Management monitoring → Technical monitoring → 3D design concept → Value creation → Risks → Final message.*

The arc starts in the lab (a researcher counting nuclei by hand), moves to the system that replaces that work, opens up the engineering and project-management discipline behind it, and closes on the value created and what the team has learned.

## Slide-by-slide plan

| # | Slide title | Speaking time | Main message | Suggested presenter |
|---|---|---|---|---|
| 1 | Title & team | 0:25 | Project name, course, 4-member team (with the instructor's approval), one-line tagline. | M1 |
| 2 | Hook — "counting nuclei by hand" | 0:30 | A researcher counts thousands of nuclei manually. It is slow, inconsistent, hard to scale. | M1 |
| 3 | Problem statement | 0:30 | Three pain points: speed, consistency, scale — plus the need to monitor project execution and system performance. | M1 |
| 4 | Proposed solution | 0:35 | Web-based AI platform: upload → segment → count → visualise → export. Anchored on a U-Net we already trained. | M2 |
| 5 | System workflow & architecture | 0:50 | Layered architecture: React frontend → FastAPI → service layer → AI module → SQLModel/Postgres + object storage. Show the flow of one image through the system. | M2 |
| 6 | AI pipeline & demo snapshot | 0:40 | U-Net + thresholding + connected components → count + density heatmap + morphology. Show real outputs from the repo. | M3 |
| 7 | Management monitoring | 0:30 | The 9 management metrics; how the weekly status report keeps the project honest under a 4-person team. | M1 |
| 8 | Technical monitoring | 0:30 | The 11 runtime metrics; thresholds; canary inference; how monitoring closes the loop on quality. | M2 / M3 |
| 9 | 3D design concept | 0:35 | Glassmorphism, depth, layered panels, isometric workflow illustration, hero illustration. Show the Figma mockup set. Explicitly: **proposed**. | M4 |
| 10 | Value creation | 0:25 | Customer, business, functional, operational, technical value — one line each. | M4 |
| 11 | Risks & how we handle them | 0:25 | The 4-vs-6–8 compliance risk, model accuracy in dense regions, schedule, video permission. | M1 |
| 12 | Final message & thanks | 0:25 | What we built, what we monitored, what we learned. Invite questions. | M1 |

**Total:** 25 + 30 + 30 + 35 + 50 + 40 + 30 + 30 + 35 + 25 + 25 + 25 = **380 s ≈ 6:20**, leaving a 40-second safety margin under the 7:00 cap.

## Delivery rules

- **Hard cap.** If the team is over budget at any rehearsal, cut bullets — never add slides.
- **Two timed dry runs.** Required in the final two weeks (see `MANAGEMENT_MONITORING_PLAN.md` metric #5).
- **One slide, one idea.** No paragraphs on slides. Speaker notes carry the detail.
- **Demo evidence.** Slide 6 uses outputs already in `outputs/` (overlays, density maps, morphology summary) so we are showing real, verified results.
- **3D framing.** On slide 9, M4 explicitly says "proposed design concept" so evaluators do not expect a running 3D engine.
- **Hand-off cues.** Each presenter ends with a one-sentence cue ("…and that brings me to monitoring — over to M2").
- **Backup video.** Recorded version of this exact deck, with the same timing, is uploaded ahead of the deadline (see `FINAL_SUBMISSION_CHECKLIST.md`).
- **Slide-9 fail-safe.** If the live Figma link does not render, M4 falls back to a backup screenshot embedded in the deck (see `UI_3D_DESIGN_CONCEPT.md`).

---

*Document version: v0.2 — 2026-05-01*

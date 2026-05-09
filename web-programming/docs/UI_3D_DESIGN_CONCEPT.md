# UI 3D Design Concept

**Project:** AI-Powered Microscopy Analysis System for Nuclei Segmentation and Cell Counting
**Course:** Software Project Management & Technical Monitoring
**Owner:** M4 — UX/UI Designer + QA/Testing Lead
**Implementation status:** **Proposed / conceptual** for this term. Recommended deliverable is a Figma mockup set + a glassmorphism CSS tokens file ready to plug into the planned React + Vite + TypeScript dashboard.

## Executive summary

This document specifies the 3D-inspired visual language for the dashboard: glassmorphism surfaces, a defined depth-shadow scale, an isometric workflow diagram, and a small set of layered components used consistently across the six application pages. Concrete design tokens (hex colours, shadow values, blur radius, border radius, type scale) are listed in Section B so the design can be implemented without further interpretation. The status is explicitly **proposed**: deliverables are a Figma mockup set, a CSS tokens file, and a backup screenshot for slide 9 of the in-class presentation.

## Slide-9 speaker line (35 seconds)

> "We designed a 3D-inspired visual language for the dashboard, built on glassmorphism, a three-stop depth-shadow scale, and an isometric workflow diagram of the AI pipeline. It is a proposed design concept for this term, delivered as a Figma mockup set and a CSS tokens file ready to plug into the planned React frontend."

If the Figma link does not render in class, M4 falls back to **a backup screenshot embedded directly in the deck** so slide 9 still shows the design.

---

## A. Design Objective

The project includes a 3D design concept for two reasons:

1. **It fits the data.** Microscopy results are inherently visual — original image, segmentation overlay, mask, density heatmap, and quantitative summary. Depth and layering let the user separate these layers in their eye instead of cramming them into a flat grid.
2. **It strengthens the report and the presentation.** A 3D-inspired visual language elevates the dashboard from "plain CRUD" to a polished SaaS feel that reads well on a slide and in a written report. It signals product thinking, not just code.

The 3D design adds: a clearer visual hierarchy on the dashboard; an isometric workflow diagram that explains the AI pipeline at a glance; layered panels that group monitoring metrics; and a hero illustration that gives the landing page identity.

It is **not** a 3D rendering engine; the system does not run WebGL geometry. Treat "3D" here as a 3D-inspired visual language.

## B. Design Style

| Element | Direction |
|---|---|
| **Colour direction** | Deep neutral background; layered translucent surfaces (glassmorphism); accent gradient running cool→warm reserved for primary CTAs and key metrics. |
| **Depth & shadow usage** | Three-stop shadow scale (rest / hover / focus). Surfaces sit on a virtual z-axis: background → main panel → floating card → modal. No flat single-shade shadows. |
| **3D / isometric visual style** | Isometric (≈30°) for explanatory diagrams (workflow, architecture). Faux-3D (depth cards with subtle parallax) for dashboard tiles. No real 3D models. |
| **Cards and panels** | Glassmorphism: translucent backdrop blur, 1 px hairline border, soft inner highlight on the top edge. Cards float above the page; panels group cards. |
| **Typography direction** | One sans-serif family across the app (Inter as primary). Tabular numerics for metric tiles. Generous line height; no all-caps body. |
| **Interaction feel** | Subtle elevation change on hover, ease-out transitions ≤ 200 ms, no bouncy spring. Focus rings always visible for accessibility. |

### B.1 Concrete design tokens

The values below are the source of truth for the Figma mockup set and the CSS tokens file. They are concrete enough to be implemented without further interpretation.

**Colour palette**

| Token | Hex | Usage |
|---|---|---|
| `--bg-base` | `#0B0F1A` | Page background |
| `--bg-elevated` | `#121826` | Main panels |
| `--surface-glass` | `rgba(255, 255, 255, 0.06)` | Glassmorphism card background |
| `--border-hairline` | `rgba(255, 255, 255, 0.10)` | 1 px card borders |
| `--text-primary` | `#E6ECF5` | Body and headings |
| `--text-muted` | `#8A95AA` | Captions, secondary labels |
| `--accent-teal` | `#14B8A6` | Gradient stop 1 (cool) |
| `--accent-violet` | `#7C3AED` | Gradient stop 2 (mid) |
| `--accent-coral` | `#F97066` | Gradient stop 3 (warm) |
| `--status-green` | `#22C55E` | 🟢 |
| `--status-amber` | `#F59E0B` | 🟡 |
| `--status-red` | `#EF4444` | 🔴 |

**Shadow scale (three stops)**

| Token | Value | Used for |
|---|---|---|
| `--shadow-rest` | `0 4px 12px rgba(0, 0, 0, 0.18)` | Resting card elevation |
| `--shadow-hover` | `0 8px 24px rgba(0, 0, 0, 0.28)` | Hover/focus elevation |
| `--shadow-modal` | `0 24px 48px rgba(0, 0, 0, 0.40)` | Modals and active stage glow |

**Geometry & motion**

| Token | Value |
|---|---|
| `--radius-card` | `16px` |
| `--radius-tile` | `12px` |
| `--radius-input` | `10px` |
| `--blur-glass` | `backdrop-filter: blur(16px) saturate(140%)` |
| `--border-card` | `1px solid var(--border-hairline)` |
| `--motion-fast` | `150ms ease-out` |
| `--motion-base` | `200ms ease-out` |
| `--focus-ring` | `0 0 0 2px var(--accent-violet)` |

**Type scale**

| Role | Family | Size / Weight |
|---|---|---|
| Display (hero) | Inter | 48 / 700 |
| H1 | Inter | 32 / 600 |
| H2 | Inter | 24 / 600 |
| Body | Inter | 16 / 400 |
| Caption | Inter | 13 / 500 |
| Metric tile (tabular) | Inter | 28 / 600, `font-variant-numeric: tabular-nums` |

## C. Pages with 3D Design

| Page | 3D-inspired treatment |
|---|---|
| **Landing / home page** | Full-bleed hero with a 3D-style illustration of a microscope or nuclei field rendered in the accent gradient. Scrolling reveals isometric workflow diagram (upload → segment → count → report). |
| **Login page** | Floating glassmorphism card centred on a soft gradient backdrop. Form field focus uses the depth shadow scale. |
| **Upload page** | Drop zone is a layered panel with a subtle floating shadow; on drag-over, the panel rises one shadow step to confirm receipt. |
| **Analysis status page** | Pipeline stages (preprocess → predict → postprocess → count) shown as connected isometric blocks; the active stage glows with the accent gradient. |
| **Results page** | Side-by-side floating cards for original image, overlay, mask, heatmap. Quantitative summary tiles (count, average area, density) use depth and tabular numerics. |
| **Monitoring dashboard** | Layered panels grouping management vs. technical metrics. Each metric tile uses the same depth shadow scale; status colour (🟢/🟡/🔴) is reinforced by a soft inner glow. |

## D. 3D UI Elements

- **Floating cards** — primary container for any single metric or result.
- **Layered panels** — groups of related cards on the monitoring and results pages.
- **Isometric workflow diagram** — explains the AI pipeline on the landing page and slide 5 of the presentation. Specification below.
- **3D-style data widgets** — count, density, morphology tiles with depth shadow and tabular numerics.
- **Hero illustration** — landing page identity asset, gradient-tinted, faux-3D microscope or nuclei motif.
- **3D icons / illustration style** — consistent flat-with-depth style across nav and empty states.
- **Result summary tiles with depth** — quick-read "headline" numbers above the detail tables.
- **Visualization frame for segmentation outputs** — the overlay/mask/heatmap viewer sits inside a layered panel.

### D.1 Isometric workflow diagram — specification

The diagram is the canonical visual that appears on the landing page, on slide 5 of the presentation, and (cropped) at the top of Section 5 of the report. It shows four blocks connected by arrows reading left to right:

| Stage | Block label | Icon hint | Active-state colour |
|---|---|---|---|
| 1 | **Upload** | cloud-up | `--accent-teal` |
| 2 | **Segment** (U-Net) | grid / mask | `--accent-violet` |
| 3 | **Count** (connected components) | counter / dots | `--accent-violet` |
| 4 | **Report** (overlay + heatmap + CSV) | document / chart | `--accent-coral` |

- **Projection.** Isometric, ~30° axes, equal block sizes.
- **Connectors.** Right-pointing arrows between adjacent blocks; arrow heads filled with `--text-muted`.
- **Active state.** The currently running stage uses `--shadow-modal` plus a 2 px outer glow in the stage colour; inactive stages use `--shadow-rest` and `--text-muted` outlines.
- **Asset format.** Vector SVG, embeddable in both the dashboard and the slide deck. A PNG export is kept beside the SVG as a fallback for environments that do not render SVGs.

## E. Report and Presentation Usage

| Surface | How the 3D design is shown |
|---|---|
| **Project report** | Section 9 (Basic UI / Dashboard Design) and Section 10 (3D Design Concept) embed the Figma mockups as images, with a one-line caption per page. The "Proposed" status is stated explicitly. |
| **In-class presentation** | Slide 9 is the dedicated 3D design slide; slides 4 and 6 reuse the isometric workflow diagram and floating result tiles to keep the visual language consistent across the deck. |
| **Backup video** | The same slide deck is recorded; M4 narrates the 3D concept slide and explicitly says "proposed design concept" so evaluators do not expect a live 3D engine. |

## F. Implementation Note

- **Status:** **Proposed / conceptual** for this term.
- **What is delivered:** a Figma mockup set covering the six pages above, plus a small CSS tokens file (colour, shadow scale, blur radius, border radius, type scale) that can be dropped into the planned React + Vite + TypeScript dashboard.
- **What is not delivered:** an interactive 3D engine, custom WebGL components, or production rendering. These are out of scope for the course.
- **How to present this professionally:** lead with "we designed a 3D-inspired visual language and delivered it as a mockup + CSS direction," then show the mockups. This is honest and reads as a deliberate scope decision, not a missing feature.

## G. Optional Practical Recommendations

If a frontend is added during the term:

- **Where 3D-inspired styles fit cheapest first.** Start with the metric tiles on the results and monitoring pages; one shadow scale + one card component covers most of the visual win.
- **Assets to add.** One hero illustration; one isometric workflow diagram; one 3D-style 404 or empty-state illustration.
- **Avoid scope creep.** Do not introduce a real 3D engine, animated particle backgrounds, or a custom shader pipeline. Glassmorphism + depth shadows + isometric SVGs are enough to read as "3D design" in the report and slides.
- **Reuse the Streamlit prototype.** The existing `src/app.py` already has the right page list (upload → segment → count → density → morphology). The mockup set should mirror that flow so the visual language is consistent with the working demo.

---

*Document version: v0.2 — 2026-05-01*

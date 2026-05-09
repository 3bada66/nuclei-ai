from pathlib import Path
import os
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = ROOT / "outputs" / "report4_evidence"
COUNTING_DIR = EVIDENCE_DIR / "counting"
DENSITY_DIR = EVIDENCE_DIR / "density"
MORPHOLOGY_DIR = EVIDENCE_DIR / "morphology"
OVERLAY_DIR = EVIDENCE_DIR / "overlays"
PRED_MASK_DIR = EVIDENCE_DIR / "pred_masks"
PROTOTYPE_DIR = EVIDENCE_DIR / "prototype"

PROTOTYPE_DIR.mkdir(parents=True, exist_ok=True)

COUNT_RESULTS = COUNTING_DIR / "count_results.csv"
COUNT_SUMMARY = COUNTING_DIR / "count_summary.txt"
MORPH_SUMMARY = MORPHOLOGY_DIR / "morphology_summary.csv"
DENSITY_SUMMARY = DENSITY_DIR / "density_summary.csv"

CASES = [
    "TCGA-AR-A1AK-01Z-00-DX1",
    "TCGA-38-6178-01Z-00-DX1",
    "TCGA-HE-7129-01Z-00-DX1",
    "TCGA-HE-7130-01Z-00-DX1",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return f"Missing file: {path}"

    return path.read_text(encoding="utf-8", errors="ignore")


def table_from_csv(path: Path, max_rows: int = 10) -> str:
    if not path.exists():
        return f"<p><b>Missing file:</b> {path}</p>"

    df = pd.read_csv(path)
    return df.head(max_rows).to_html(index=False, border=0, classes="data-table")


def case_count_table() -> str:
    if not COUNT_RESULTS.exists():
        return "<p>count_results.csv not found.</p>"

    df = pd.read_csv(COUNT_RESULTS)

    if "image_name" not in df.columns:
        return "<p>image_name column not found in count_results.csv.</p>"

    df = df[df["image_name"].isin(CASES)]

    cols = [
        "image_name",
        "predicted_count",
        "ground_truth_count",
        "absolute_error",
        "squared_error",
    ]

    available_cols = [col for col in cols if col in df.columns]

    if len(available_cols) == 0:
        return "<p>No expected count columns found.</p>"

    return df[available_cols].to_html(index=False, border=0, classes="data-table")


def image_tag(path: Path, title: str) -> str:
    if not path.exists():
        return f"<div class='missing'>Missing: {path.name}</div>"

    # The dashboard HTML is saved inside:
    # outputs/report4_evidence/prototype/
    # Images are stored in sibling folders:
    # outputs/report4_evidence/overlays/
    # outputs/report4_evidence/pred_masks/
    # outputs/report4_evidence/density/
    # Therefore we need paths like ../overlays/image.png
    rel_path = os.path.relpath(path, PROTOTYPE_DIR).replace("\\", "/")

    return f"""
    <div class="image-card">
        <h4>{title}</h4>
        <img src="{rel_path}" alt="{title}">
    </div>
    """


def build_case_block(case_name: str) -> str:
    overlay = OVERLAY_DIR / f"{case_name}_overlay.png"
    pred_mask = PRED_MASK_DIR / f"{case_name}_pred_mask.png"
    density = DENSITY_DIR / f"{case_name}_density_heatmap.png"

    return f"""
    <section class="case-block">
        <h3>{case_name}</h3>
        <div class="image-grid">
            {image_tag(overlay, "Overlay")}
            {image_tag(pred_mask, "Predicted Mask")}
            {image_tag(density, "Density Heatmap")}
        </div>
    </section>
    """


def main():
    print("Building Report 4 prototype dashboard...")

    required_files = [
        COUNT_RESULTS,
        COUNT_SUMMARY,
        MORPH_SUMMARY,
        DENSITY_SUMMARY,
    ]

    missing = [str(path) for path in required_files if not path.exists()]

    if missing:
        print("Warning: missing files:")
        for item in missing:
            print(" -", item)

    count_summary_text = read_text(COUNT_SUMMARY)
    case_blocks = "\n".join(build_case_block(case) for case in CASES)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Report 4 Prototype Dashboard</title>

    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 32px;
            background: #f7f7f7;
            color: #111;
        }}

        h1, h2, h3 {{
            color: #0b1f3a;
        }}

        .card {{
            background: white;
            padding: 20px;
            margin-bottom: 24px;
            border-radius: 12px;
            border: 1px solid #ddd;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }}

        pre {{
            background: #111;
            color: #f1f1f1;
            padding: 16px;
            border-radius: 8px;
            white-space: pre-wrap;
            overflow-x: auto;
        }}

        .data-table {{
            border-collapse: collapse;
            width: 100%;
            background: white;
            margin-top: 12px;
        }}

        .data-table th,
        .data-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            font-size: 14px;
        }}

        .data-table th {{
            background: #e8eef8;
            text-align: left;
        }}

        .case-block {{
            background: white;
            padding: 20px;
            margin-bottom: 24px;
            border-radius: 12px;
            border: 1px solid #ddd;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }}

        .image-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}

        .image-card {{
            background: #fafafa;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #ddd;
        }}

        .image-card h4 {{
            margin-top: 0;
            margin-bottom: 10px;
        }}

        .image-card img {{
            width: 100%;
            max-height: 320px;
            object-fit: contain;
            border: 1px solid #ccc;
            background: white;
        }}

        .missing {{
            padding: 16px;
            background: #ffe0e0;
            border: 1px solid #cc0000;
            border-radius: 8px;
            color: #800000;
            font-weight: bold;
        }}

        .note {{
            background: #fff8dc;
            padding: 12px;
            border-left: 5px solid #d69e00;
            margin-top: 12px;
        }}

        .small {{
            font-size: 14px;
            color: #444;
        }}
    </style>
</head>

<body>
    <h1>Report 4 Prototype Dashboard</h1>

    <div class="card">
        <h2>Project</h2>
        <p><b>AI-Based Cell Nuclei Segmentation and Counting in Microscopy Images</b></p>
        <p>
            This dashboard integrates the corrected counting pipeline, density heatmap outputs,
            morphology features, and qualitative visual evidence for Progress Report 4.
        </p>

        <div class="note">
            Corrected baseline used for Report 4:
            <b>Threshold = 0.8</b>,
            <b>MIN_AREA = 1 for counting</b>,
            and <b>XML-based ground-truth counts</b>.
            Morphology uses <b>MIN_AREA = 5</b> only to make shape measurements more stable.
        </div>
    </div>

    <div class="card">
        <h2>Counting Summary</h2>
        <pre>{count_summary_text}</pre>
    </div>

    <div class="card">
        <h2>Selected Best/Worst Counting Cases</h2>
        <p class="small">
            These cases are selected from the corrected XML-based evaluation and are used
            as qualitative evidence in Report 4.
        </p>
        {case_count_table()}
    </div>

    <div class="card">
        <h2>Morphology Summary Preview</h2>
        <p class="small">
            Morphology features include area, perimeter, circularity, eccentricity,
            centroid coordinates, and bounding-box values.
        </p>
        {table_from_csv(MORPH_SUMMARY, max_rows=8)}
    </div>

    <div class="card">
        <h2>Density Summary Preview</h2>
        <p class="small">
            Density heatmaps summarize predicted nuclei distribution using grid-based tile counts.
        </p>
        {table_from_csv(DENSITY_SUMMARY, max_rows=8)}
    </div>

    <div class="card">
        <h2>Qualitative Visual Evidence</h2>
        <p>
            Each selected case includes overlay visualization, predicted mask, and density heatmap.
        </p>
    </div>

    {case_blocks}

</body>
</html>
"""

    out_path = PROTOTYPE_DIR / "report4_dashboard.html"
    out_path.write_text(html, encoding="utf-8")

    print("Done.")
    print(f"Dashboard saved to: {out_path}")


if __name__ == "__main__":
    main()
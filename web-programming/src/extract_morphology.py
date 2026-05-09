from pathlib import Path
import math

import cv2
import numpy as np
import pandas as pd
from skimage.measure import label, regionprops


ROOT = Path(__file__).resolve().parent.parent

PRED_MASK_DIR = ROOT / "outputs" / "counting_batch_refined_xmlgt" / "pred_masks"
OUTPUT_DIR = ROOT / "outputs" / "morphology"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# For morphology only.
# Counting baseline still uses MIN_AREA = 1 from Report 3.
# Morphology uses MIN_AREA = 5 to avoid unstable shape measurements from tiny noisy objects.
MIN_AREA = 5


def load_binary_mask(mask_path: Path) -> np.ndarray:
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    if mask is None:
        raise RuntimeError(f"Could not read mask: {mask_path}")

    binary = (mask > 0).astype(np.uint8)
    return binary


def get_perimeter(region) -> float:
    return float(getattr(region, "perimeter_crofton", region.perimeter))


def compute_circularity(area: float, perimeter: float) -> float:
    if perimeter <= 0:
        return 0.0

    value = float((4.0 * math.pi * area) / (perimeter ** 2))

    # Circularity is normally interpreted in the range 0–1.
    # Small irregular components can produce unstable values, so we cap it at 1.
    return min(value, 1.0)


def main():
    print("Extracting morphology features...")
    print(f"Predicted masks folder: {PRED_MASK_DIR}")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Morphology MIN_AREA: {MIN_AREA}")

    if not PRED_MASK_DIR.exists():
        raise FileNotFoundError(
            f"Predicted mask folder not found: {PRED_MASK_DIR}\n"
            "Run the corrected XML-based batch counting first."
        )

    mask_paths = sorted(PRED_MASK_DIR.glob("*_pred_mask.png"))

    if len(mask_paths) == 0:
        raise RuntimeError(f"No predicted masks found in: {PRED_MASK_DIR}")

    object_rows = []
    summary_rows = []

    for mask_path in mask_paths:
        image_name = mask_path.name.replace("_pred_mask.png", "")

        binary_mask = load_binary_mask(mask_path)
        labeled_mask = label(binary_mask, connectivity=2)

        regions = regionprops(labeled_mask)
        valid_regions = []

        for region in regions:
            area = float(region.area)

            if area < MIN_AREA:
                continue

            perimeter = get_perimeter(region)
            circularity = compute_circularity(area, perimeter)
            eccentricity = float(region.eccentricity)

            centroid_y, centroid_x = region.centroid
            min_row, min_col, max_row, max_col = region.bbox

            valid_regions.append(region)

            object_rows.append({
                "image_name": image_name,
                "component_id": int(region.label),
                "area": round(area, 4),
                "perimeter": round(perimeter, 4),
                "circularity": round(circularity, 4),
                "eccentricity": round(eccentricity, 4),
                "centroid_x": round(float(centroid_x), 4),
                "centroid_y": round(float(centroid_y), 4),
                "bbox_min_row": int(min_row),
                "bbox_min_col": int(min_col),
                "bbox_max_row": int(max_row),
                "bbox_max_col": int(max_col)
            })

        if len(valid_regions) > 0:
            areas = [float(r.area) for r in valid_regions]
            perimeters = [get_perimeter(r) for r in valid_regions]
            eccentricities = [float(r.eccentricity) for r in valid_regions]
            circularities = [
                compute_circularity(float(r.area), get_perimeter(r))
                for r in valid_regions
            ]

            summary_rows.append({
                "image_name": image_name,
                "predicted_components_after_morphology_filter": len(valid_regions),
                "morphology_min_area": MIN_AREA,
                "mean_area": round(float(np.mean(areas)), 4),
                "median_area": round(float(np.median(areas)), 4),
                "mean_perimeter": round(float(np.mean(perimeters)), 4),
                "mean_circularity": round(float(np.mean(circularities)), 4),
                "mean_eccentricity": round(float(np.mean(eccentricities)), 4),
                "min_area": round(float(np.min(areas)), 4),
                "max_area": round(float(np.max(areas)), 4)
            })
        else:
            summary_rows.append({
                "image_name": image_name,
                "predicted_components_after_morphology_filter": 0,
                "morphology_min_area": MIN_AREA,
                "mean_area": 0,
                "median_area": 0,
                "mean_perimeter": 0,
                "mean_circularity": 0,
                "mean_eccentricity": 0,
                "min_area": 0,
                "max_area": 0
            })

    object_df = pd.DataFrame(object_rows)
    summary_df = pd.DataFrame(summary_rows)

    object_csv = OUTPUT_DIR / "morphology_results.csv"
    summary_csv = OUTPUT_DIR / "morphology_summary.csv"

    object_df.to_csv(object_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)

    print("Done.")
    print(f"Processed masks: {len(mask_paths)}")
    print(f"Total extracted morphology components: {len(object_df)}")
    print(f"Morphology object table saved to: {object_csv}")
    print(f"Morphology summary saved to: {summary_csv}")


if __name__ == "__main__":
    main()
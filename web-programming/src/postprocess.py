from pathlib import Path
import sys

import cv2
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

BASE_NAME = "TCGA-18-5592-01Z-00-DX1"

PRED_MASK_PATH = ROOT / f"outputs/inference/{BASE_NAME}_pred_mask.png"
GT_MASK_PATH = ROOT / f"data/processed/masks/{BASE_NAME}.png"

OUTPUT_DIR = ROOT / "outputs/counting"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_AREA = 5  # ignore very tiny noisy components


def count_nuclei(mask_path, min_area=5):
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    if mask is None:
        raise ValueError(f"Failed to read mask: {mask_path}")

    binary = (mask > 0).astype("uint8")

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    count = 0
    for label_id in range(1, num_labels):  # skip background
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area >= min_area:
            count += 1

    return count


def main():
    pred_count = count_nuclei(PRED_MASK_PATH, min_area=MIN_AREA)
    gt_count = count_nuclei(GT_MASK_PATH, min_area=MIN_AREA)

    abs_error = abs(pred_count - gt_count)
    sq_error = (pred_count - gt_count) ** 2

    df = pd.DataFrame([
        {
            "image_name": BASE_NAME,
            "predicted_count": pred_count,
            "ground_truth_count": gt_count,
            "absolute_error": abs_error,
            "squared_error": sq_error,
        }
    ])

    csv_path = OUTPUT_DIR / "count_results.csv"
    txt_path = OUTPUT_DIR / "count_summary.txt"

    df.to_csv(csv_path, index=False)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Image: {BASE_NAME}\n")
        f.write(f"Predicted count: {pred_count}\n")
        f.write(f"Ground truth count: {gt_count}\n")
        f.write(f"Absolute error: {abs_error}\n")
        f.write(f"Squared error: {sq_error}\n")

    print("Done.")
    print(f"Predicted count: {pred_count}")
    print(f"Ground truth count: {gt_count}")
    print(f"Absolute error: {abs_error}")
    print(f"Squared error: {sq_error}")
    print(f"CSV saved to: {csv_path}")
    print(f"Summary saved to: {txt_path}")


if __name__ == "__main__":
    main()
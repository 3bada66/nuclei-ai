from pathlib import Path
import sys

import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
import segmentation_models_pytorch as smp

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.dataset import NucleiDataset

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

VAL_CSV = ROOT / "data/splits/val.csv"
GT_COUNTS_CSV = ROOT / "outputs/ground_truth/ground_truth_counts.csv"
CHECKPOINT_PATH = ROOT / "outputs/checkpoints/best_model.pth"

OUTPUT_DIR = ROOT / "outputs/threshold_tuning_xmlgt"
PER_IMAGE_DIR = OUTPUT_DIR / "per_image"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = 256
BATCH_SIZE = 1
NUM_WORKERS = 0

THRESHOLDS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
MIN_AREA = 1


def count_nuclei(binary_mask: np.ndarray, min_area: int = 1) -> int:
    binary_mask = binary_mask.astype("uint8")

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary_mask, connectivity=8
    )

    count = 0
    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area >= min_area:
            count += 1

    return count


def load_model() -> torch.nn.Module:
    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    ).to(DEVICE)

    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=DEVICE))
    model.eval()
    return model


def main():
    print(f"Using device: {DEVICE}")
    print(f"Testing thresholds: {THRESHOLDS}")
    print(f"MIN_AREA fixed at: {MIN_AREA}")

    if not VAL_CSV.exists():
        raise FileNotFoundError(f"Validation CSV not found: {VAL_CSV}")

    if not GT_COUNTS_CSV.exists():
        raise FileNotFoundError(f"Ground-truth CSV not found: {GT_COUNTS_CSV}")

    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")

    gt_df = pd.read_csv(GT_COUNTS_CSV)
    gt_map = dict(zip(gt_df["image_name"], gt_df["ground_truth_count_xml"]))

    val_dataset = NucleiDataset(VAL_CSV, image_size=IMAGE_SIZE)
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    model = load_model()

    cached_probs = []

    with torch.no_grad():
        for idx, (images, masks) in enumerate(tqdm(val_loader, desc="Preparing probabilities")):
            images = images.to(DEVICE)

            logits = model(images)
            probs = torch.sigmoid(logits)[0, 0].detach().cpu().numpy()

            image_name = Path(val_dataset.df.iloc[idx]["image_path"]).stem

            if image_name not in gt_map:
                raise KeyError(f"Missing XML ground truth count for image: {image_name}")

            gt_count = int(gt_map[image_name])

            cached_probs.append({
                "image_name": image_name,
                "probs": probs,
                "ground_truth_count": gt_count,
            })

    summary_rows = []

    for threshold in THRESHOLDS:
        rows = []

        for item in cached_probs:
            pred_mask = (item["probs"] > threshold).astype("uint8")
            pred_count = count_nuclei(pred_mask, min_area=MIN_AREA)
            gt_count = item["ground_truth_count"]

            abs_error = abs(pred_count - gt_count)
            sq_error = (pred_count - gt_count) ** 2

            rows.append({
                "image_name": item["image_name"],
                "predicted_count": pred_count,
                "ground_truth_count": gt_count,
                "absolute_error": abs_error,
                "squared_error": sq_error,
            })

        df = pd.DataFrame(rows)

        mae = df["absolute_error"].mean()
        mse = df["squared_error"].mean()

        threshold_str = str(threshold).replace(".", "_")
        per_image_path = PER_IMAGE_DIR / f"threshold_{threshold_str}.csv"
        df.to_csv(per_image_path, index=False)

        summary_rows.append({
            "threshold": threshold,
            "mae": round(mae, 4),
            "mse": round(mse, 4),
        })

    summary_df = pd.DataFrame(summary_rows).sort_values("threshold")
    summary_csv_path = OUTPUT_DIR / "threshold_summary.csv"
    summary_txt_path = OUTPUT_DIR / "threshold_summary.txt"

    summary_df.to_csv(summary_csv_path, index=False)

    best_mae_row = summary_df.sort_values("mae").iloc[0]
    best_mse_row = summary_df.sort_values("mse").iloc[0]

    with open(summary_txt_path, "w", encoding="utf-8") as f:
        f.write("Threshold tuning summary (XML ground truth)\n")
        f.write(f"MIN_AREA: {MIN_AREA}\n\n")
        f.write(summary_df.to_string(index=False))
        f.write("\n\n")
        f.write(
            f"Best threshold by MAE: {best_mae_row['threshold']:.1f} "
            f"(MAE={best_mae_row['mae']:.4f})\n"
        )
        f.write(
            f"Best threshold by MSE: {best_mse_row['threshold']:.1f} "
            f"(MSE={best_mse_row['mse']:.4f})\n"
        )

    print("\nDone.")
    print(summary_df.to_string(index=False))
    print()
    print(
        f"Best threshold by MAE: {best_mae_row['threshold']:.1f} "
        f"(MAE={best_mae_row['mae']:.4f})"
    )
    print(
        f"Best threshold by MSE: {best_mse_row['threshold']:.1f} "
        f"(MSE={best_mse_row['mse']:.4f})"
    )
    print(f"\nSummary CSV saved to: {summary_csv_path}")
    print(f"Summary TXT saved to: {summary_txt_path}")
    print(f"Per-image CSV files saved to: {PER_IMAGE_DIR}")


if __name__ == "__main__":
    main()
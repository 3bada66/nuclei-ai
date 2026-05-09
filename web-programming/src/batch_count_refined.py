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

# Use all 37 images
VAL_CSV = ROOT / "data/splits/all.csv"

# XML-based ground-truth counts
GT_COUNTS_CSV = ROOT / "outputs/ground_truth/ground_truth_counts.csv"

CHECKPOINT_PATH = ROOT / "outputs/checkpoints/best_model.pth"

OUTPUT_DIR = ROOT / "outputs/counting_batch_refined_xmlgt"
PRED_MASK_DIR = OUTPUT_DIR / "pred_masks"
OVERLAY_DIR = OUTPUT_DIR / "overlays"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PRED_MASK_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = 256
BATCH_SIZE = 1
NUM_WORKERS = 0

# Corrected operating point from XML-based threshold tuning
THRESHOLD = 0.8
MIN_AREA = 1


def count_nuclei_from_binary(binary_mask: np.ndarray, min_area: int = 1) -> int:
    binary_mask = binary_mask.astype("uint8")

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary_mask, connectivity=8
    )

    count = 0
    for label_id in range(1, num_labels):  # skip background
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area >= min_area:
            count += 1

    return count


def tensor_to_uint8_image(image_tensor: torch.Tensor) -> np.ndarray:
    image_np = image_tensor.detach().cpu().permute(1, 2, 0).numpy()

    img_min = image_np.min()
    img_max = image_np.max()

    if img_max > img_min:
        image_np = (image_np - img_min) / (img_max - img_min)
    else:
        image_np = np.zeros_like(image_np)

    image_uint8 = (image_np * 255).clip(0, 255).astype("uint8")
    return image_uint8


def save_overlay(image_uint8: np.ndarray, pred_mask: np.ndarray, save_path: Path) -> None:
    overlay = image_uint8.copy()

    red = np.array([255, 0, 0], dtype=np.uint8)
    mask_bool = pred_mask.astype(bool)

    overlay[mask_bool] = (
        0.6 * overlay[mask_bool] + 0.4 * red
    ).astype(np.uint8)

    overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(save_path), overlay_bgr)


def main():
    print(f"Using device: {DEVICE}")
    print(f"Threshold: {THRESHOLD}")
    print(f"MIN_AREA: {MIN_AREA}")

    if not VAL_CSV.exists():
        raise FileNotFoundError(f"CSV not found: {VAL_CSV}")

    if not GT_COUNTS_CSV.exists():
        raise FileNotFoundError(f"Ground-truth CSV not found: {GT_COUNTS_CSV}")

    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")

    gt_df = pd.read_csv(GT_COUNTS_CSV)
    gt_map = dict(zip(gt_df["image_name"], gt_df["ground_truth_count_xml"]))

    dataset = NucleiDataset(VAL_CSV, image_size=IMAGE_SIZE)
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    ).to(DEVICE)

    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=DEVICE))
    model.eval()

    rows = []

    with torch.no_grad():
        for idx, (images, masks) in enumerate(tqdm(loader, desc="Batch counting")):
            images = images.to(DEVICE)

            logits = model(images)
            probs = torch.sigmoid(logits)
            preds = (probs > THRESHOLD).float()

            pred_mask = preds[0, 0].detach().cpu().numpy().astype("uint8")

            image_name = Path(dataset.df.iloc[idx]["image_path"]).stem

            if image_name not in gt_map:
                raise KeyError(f"Missing XML ground truth count for image: {image_name}")

            pred_count = count_nuclei_from_binary(pred_mask, min_area=MIN_AREA)
            gt_count = int(gt_map[image_name])

            abs_error = abs(pred_count - gt_count)
            sq_error = (pred_count - gt_count) ** 2

            pred_mask_path = PRED_MASK_DIR / f"{image_name}_pred_mask.png"
            cv2.imwrite(str(pred_mask_path), pred_mask * 255)

            image_uint8 = tensor_to_uint8_image(images[0])
            overlay_path = OVERLAY_DIR / f"{image_name}_overlay.png"
            save_overlay(image_uint8, pred_mask, overlay_path)

            rows.append({
                "image_name": image_name,
                "predicted_count": pred_count,
                "ground_truth_count": gt_count,
                "absolute_error": abs_error,
                "squared_error": sq_error,
            })

    df = pd.DataFrame(rows)

    mae = df["absolute_error"].mean()
    mse = df["squared_error"].mean()

    best_row = df.sort_values("absolute_error").iloc[0]
    worst_row = df.sort_values("absolute_error", ascending=False).iloc[0]

    csv_path = OUTPUT_DIR / "count_results.csv"
    txt_path = OUTPUT_DIR / "count_summary.txt"

    df.to_csv(csv_path, index=False)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Counting summary (XML ground truth)\n")
        f.write(f"Threshold: {THRESHOLD}\n")
        f.write(f"MIN_AREA: {MIN_AREA}\n")
        f.write(f"Processed images: {len(df)}\n")
        f.write(f"Average MAE: {mae:.4f}\n")
        f.write(f"Average MSE: {mse:.4f}\n\n")

        f.write("Best example:\n")
        f.write(f"Image: {best_row['image_name']}\n")
        f.write(f"Predicted count: {best_row['predicted_count']}\n")
        f.write(f"Ground truth count: {best_row['ground_truth_count']}\n")
        f.write(f"Absolute error: {best_row['absolute_error']}\n")
        f.write(f"Squared error: {best_row['squared_error']}\n\n")

        f.write("Worst example:\n")
        f.write(f"Image: {worst_row['image_name']}\n")
        f.write(f"Predicted count: {worst_row['predicted_count']}\n")
        f.write(f"Ground truth count: {worst_row['ground_truth_count']}\n")
        f.write(f"Absolute error: {worst_row['absolute_error']}\n")
        f.write(f"Squared error: {worst_row['squared_error']}\n")

    print("Done.")
    print(f"Processed images: {len(df)}")
    print(f"Average MAE: {mae:.4f}")
    print(f"Average MSE: {mse:.4f}")
    print(f"CSV saved to: {csv_path}")
    print(f"Summary saved to: {txt_path}")
    print(f"Predicted masks saved to: {PRED_MASK_DIR}")
    print(f"Overlays saved to: {OVERLAY_DIR}")


if __name__ == "__main__":
    main()
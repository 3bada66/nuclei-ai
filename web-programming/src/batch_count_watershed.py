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

# إذا أردت التقييم الرسمي فقط غيّر all.csv إلى val.csv
VAL_CSV = ROOT / "data/splits/all.csv"
CHECKPOINT_PATH = ROOT / "outputs/checkpoints/best_model.pth"

OUTPUT_DIR = ROOT / "outputs/counting_batch"
PRED_MASK_DIR = OUTPUT_DIR / "pred_masks"
OVERLAY_DIR = OUTPUT_DIR / "overlays"
INSTANCE_DIR = OUTPUT_DIR / "instances"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PRED_MASK_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = 256
BATCH_SIZE = 1
NUM_WORKERS = 0
THRESHOLD = 0.5
MIN_AREA = 5

DIST_THRESH_RATIO = 0.35
OPEN_ITERS = 1
DILATE_ITERS = 2


def count_nuclei_from_binary(binary_mask, min_area=5):
    binary_mask = binary_mask.astype("uint8")

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary_mask, connectivity=8
    )

    count = 0
    for label_id in range(1, num_labels):  # skip background
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area >= min_area:
            count += 1

    return count


def count_nuclei_with_watershed(
    image_uint8,
    binary_mask,
    min_area=5,
    dist_thresh_ratio=0.35,
    open_iters=1,
    dilate_iters=2,
):
    binary_mask = (binary_mask > 0).astype("uint8")
    mask_255 = binary_mask * 255

    kernel = np.ones((3, 3), np.uint8)

    # Remove tiny noise
    opening = cv2.morphologyEx(
        mask_255, cv2.MORPH_OPEN, kernel, iterations=open_iters
    )

    # Sure background
    sure_bg = cv2.dilate(opening, kernel, iterations=dilate_iters)

    # Distance transform
    dist = cv2.distanceTransform(opening, cv2.DIST_L2, 5)

    # لو القناع شبه فارغ، ارجع للعد العادي
    if dist.max() == 0:
        count = count_nuclei_from_binary(binary_mask, min_area=min_area)
        instance_mask = np.zeros_like(binary_mask, dtype=np.int32)
        return count, instance_mask

    # Sure foreground
    _, sure_fg = cv2.threshold(
        dist,
        dist_thresh_ratio * dist.max(),
        255,
        0
    )
    sure_fg = sure_fg.astype("uint8")

    # Unknown region
    unknown = cv2.subtract(sure_bg, sure_fg)

    # Connected components for markers
    num_markers, markers = cv2.connectedComponents(sure_fg)

    markers = markers + 1
    markers[unknown == 255] = 0

    # Watershed expects 3-channel image
    image_bgr = cv2.cvtColor(image_uint8, cv2.COLOR_RGB2BGR)
    markers = cv2.watershed(image_bgr, markers)

    instance_mask = np.zeros_like(binary_mask, dtype=np.int32)

    count = 0
    next_id = 1

    for label_id in np.unique(markers):
        if label_id <= 1:
            continue

        region = (markers == label_id).astype("uint8")
        area = region.sum()

        if area >= min_area:
            instance_mask[region == 1] = next_id
            next_id += 1
            count += 1

    return count, instance_mask


def tensor_to_uint8_image(image_tensor):
    image_np = image_tensor.detach().cpu().permute(1, 2, 0).numpy()

    img_min = image_np.min()
    img_max = image_np.max()

    if img_max > img_min:
        image_np = (image_np - img_min) / (img_max - img_min)
    else:
        image_np = np.zeros_like(image_np)

    image_uint8 = (image_np * 255).clip(0, 255).astype("uint8")
    return image_uint8


def save_overlay(image_uint8, pred_mask, save_path):
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

    if not VAL_CSV.exists():
        raise FileNotFoundError(f"Validation CSV not found: {VAL_CSV}")

    val_dataset = NucleiDataset(VAL_CSV, image_size=IMAGE_SIZE)
    val_loader = DataLoader(
        val_dataset,
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
        for idx, (images, masks) in enumerate(tqdm(val_loader, desc="Batch counting")):
            images = images.to(DEVICE)
            masks = masks.to(DEVICE)

            logits = model(images)
            probs = torch.sigmoid(logits)
            preds = (probs > THRESHOLD).float()

            pred_mask = preds[0, 0].detach().cpu().numpy().astype("uint8")
            gt_mask = (masks[0, 0].detach().cpu().numpy() > 0.5).astype("uint8")

            image_uint8 = tensor_to_uint8_image(images[0])

            pred_count, instance_mask = count_nuclei_with_watershed(
                image_uint8=image_uint8,
                binary_mask=pred_mask,
                min_area=MIN_AREA,
                dist_thresh_ratio=DIST_THRESH_RATIO,
                open_iters=OPEN_ITERS,
                dilate_iters=DILATE_ITERS,
            )

            gt_count = count_nuclei_from_binary(gt_mask, min_area=MIN_AREA)

            abs_error = abs(pred_count - gt_count)
            sq_error = (pred_count - gt_count) ** 2

            image_name = Path(val_dataset.df.iloc[idx]["image_path"]).stem

            # Save predicted mask
            pred_mask_path = PRED_MASK_DIR / f"{image_name}_pred_mask.png"
            cv2.imwrite(str(pred_mask_path), pred_mask * 255)

            # Save instance mask
            instance_vis = np.zeros_like(pred_mask, dtype=np.uint8)
            instance_vis[instance_mask > 0] = 255
            instance_path = INSTANCE_DIR / f"{image_name}_instances.png"
            cv2.imwrite(str(instance_path), instance_vis)

            # Save overlay
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
    print(f"Instance masks saved to: {INSTANCE_DIR}")
    print(f"Overlays saved to: {OVERLAY_DIR}")


if __name__ == "__main__":
    main()
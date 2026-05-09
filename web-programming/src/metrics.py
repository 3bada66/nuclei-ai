from pathlib import Path
import sys

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
CHECKPOINT_PATH = ROOT / "outputs/checkpoints/best_model.pth"
OUTPUT_DIR = ROOT / "outputs/metrics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = 256
BATCH_SIZE = 1
NUM_WORKERS = 0
THRESHOLD = 0.5


def dice_score(logits, targets, threshold=0.5, smooth=1.0):
    probs = torch.sigmoid(logits)
    preds = (probs > threshold).float()

    preds = preds.contiguous().view(preds.size(0), -1)
    targets = targets.contiguous().view(targets.size(0), -1)

    intersection = (preds * targets).sum(dim=1)
    dice = (2.0 * intersection + smooth) / (
        preds.sum(dim=1) + targets.sum(dim=1) + smooth
    )

    return dice.mean().item()


def iou_score(logits, targets, threshold=0.5, smooth=1.0):
    probs = torch.sigmoid(logits)
    preds = (probs > threshold).float()

    preds = preds.contiguous().view(preds.size(0), -1)
    targets = targets.contiguous().view(targets.size(0), -1)

    intersection = (preds * targets).sum(dim=1)
    union = preds.sum(dim=1) + targets.sum(dim=1) - intersection

    iou = (intersection + smooth) / (union + smooth)
    return iou.mean().item()


def main():
    print(f"Using device: {DEVICE}")

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
        for idx, (images, masks) in enumerate(tqdm(val_loader, desc="Evaluating")):
            images = images.to(DEVICE)
            masks = masks.to(DEVICE)

            logits = model(images)

            dice = dice_score(logits, masks, threshold=THRESHOLD)
            iou = iou_score(logits, masks, threshold=THRESHOLD)

            image_name = Path(val_dataset.df.iloc[idx]["image_path"]).name

            rows.append({
                "image_name": image_name,
                "dice": dice,
                "iou": iou
            })

    df = pd.DataFrame(rows)

    avg_dice = df["dice"].mean()
    avg_iou = df["iou"].mean()

    csv_path = OUTPUT_DIR / "val_metrics.csv"
    txt_path = OUTPUT_DIR / "val_metrics_summary.txt"

    df.to_csv(csv_path, index=False)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Average Dice: {avg_dice:.4f}\n")
        f.write(f"Average IoU: {avg_iou:.4f}\n")

    print("Done.")
    print(f"Average Dice: {avg_dice:.4f}")
    print(f"Average IoU: {avg_iou:.4f}")
    print(f"Per-image metrics saved to: {csv_path}")
    print(f"Summary saved to: {txt_path}")


if __name__ == "__main__":
    main()
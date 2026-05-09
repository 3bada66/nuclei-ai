from pathlib import Path
import sys

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
import segmentation_models_pytorch as smp

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.dataset import NucleiDataset


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TRAIN_CSV = ROOT / "data/splits/train.csv"
VAL_CSV = ROOT / "data/splits/val.csv"
CHECKPOINT_DIR = ROOT / "outputs/checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = 256
BATCH_SIZE = 2
EPOCHS = 5
LEARNING_RATE = 1e-3
NUM_WORKERS = 0


class DiceLoss(nn.Module):
    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)

        probs = probs.contiguous().view(probs.size(0), -1)
        targets = targets.contiguous().view(targets.size(0), -1)

        intersection = (probs * targets).sum(dim=1)
        dice = (2.0 * intersection + self.smooth) / (
            probs.sum(dim=1) + targets.sum(dim=1) + self.smooth
        )

        return 1.0 - dice.mean()


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


def train_one_epoch(model, loader, optimizer, bce_loss, dice_loss):
    model.train()
    total_loss = 0.0

    for images, masks in tqdm(loader, desc="Training", leave=False):
        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        optimizer.zero_grad()

        logits = model(images)
        loss = bce_loss(logits, masks) + dice_loss(logits, masks)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(loader)


@torch.no_grad()
def validate(model, loader, bce_loss, dice_loss):
    model.eval()
    total_loss = 0.0
    total_dice = 0.0

    for images, masks in tqdm(loader, desc="Validation", leave=False):
        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        logits = model(images)
        loss = bce_loss(logits, masks) + dice_loss(logits, masks)

        total_loss += loss.item()
        total_dice += dice_score(logits, masks)

    avg_loss = total_loss / len(loader)
    avg_dice = total_dice / len(loader)

    return avg_loss, avg_dice


def main():
    print(f"Using device: {DEVICE}")

    train_dataset = NucleiDataset(TRAIN_CSV, image_size=IMAGE_SIZE)
    val_dataset = NucleiDataset(VAL_CSV, image_size=IMAGE_SIZE)

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

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

    bce_loss = nn.BCEWithLogitsLoss()
    dice_loss = DiceLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    best_val_loss = float("inf")

    for epoch in range(1, EPOCHS + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, bce_loss, dice_loss)
        val_loss, val_dice = validate(model, val_loader, bce_loss, dice_loss)

        print(
            f"Epoch [{epoch}/{EPOCHS}] "
            f"| train_loss: {train_loss:.4f} "
            f"| val_loss: {val_loss:.4f} "
            f"| val_dice: {val_dice:.4f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), CHECKPOINT_DIR / "best_model.pth")
            print("Saved best_model.pth")

    torch.save(model.state_dict(), CHECKPOINT_DIR / "last_model.pth")
    print("Saved last_model.pth")
    print("Training finished.")


if __name__ == "__main__":
    main()
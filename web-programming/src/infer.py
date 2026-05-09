from pathlib import Path
import sys

import cv2
import numpy as np
import torch
import segmentation_models_pytorch as smp

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

CHECKPOINT_PATH = ROOT / "outputs/checkpoints/best_model.pth"
IMAGE_PATH = ROOT / "data/processed/images/TCGA-18-5592-01Z-00-DX1.png"
OUTPUT_DIR = ROOT / "outputs/inference"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = 256
THRESHOLD = 0.5


def load_image(image_path):
    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise ValueError(f"Failed to read image: {image_path}")

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    resized_rgb = cv2.resize(image_rgb, (IMAGE_SIZE, IMAGE_SIZE))

    tensor = resized_rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = torch.tensor(tensor, dtype=torch.float32).unsqueeze(0)

    return resized_rgb, tensor


def make_overlay(image_rgb, mask):
    overlay = image_rgb.copy()
    color_mask = np.zeros_like(image_rgb)
    color_mask[mask > 0] = [255, 0, 0]  # red mask in RGB
    overlay = cv2.addWeighted(image_rgb, 0.7, color_mask, 0.3, 0)
    return overlay


def main():
    print(f"Using device: {DEVICE}")

    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    ).to(DEVICE)

    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=DEVICE))
    model.eval()

    image_rgb, image_tensor = load_image(IMAGE_PATH)
    image_tensor = image_tensor.to(DEVICE)

    with torch.no_grad():
        logits = model(image_tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()

    pred_mask = (probs > THRESHOLD).astype(np.uint8) * 255
    overlay = make_overlay(image_rgb, pred_mask)

    base_name = IMAGE_PATH.stem

    mask_path = OUTPUT_DIR / f"{base_name}_pred_mask.png"
    overlay_path = OUTPUT_DIR / f"{base_name}_overlay.png"
    input_path = OUTPUT_DIR / f"{base_name}_input.png"

    cv2.imwrite(str(mask_path), pred_mask)
    cv2.imwrite(str(overlay_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(input_path), cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))

    print("Done.")
    print(f"Input image saved to: {input_path}")
    print(f"Predicted mask saved to: {mask_path}")
    print(f"Overlay saved to: {overlay_path}")


if __name__ == "__main__":
    main()
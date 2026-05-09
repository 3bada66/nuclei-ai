from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent

PRED_MASK_DIR = ROOT / "outputs" / "counting_batch_refined_xmlgt" / "pred_masks"
ALL_CSV = ROOT / "data" / "splits" / "all.csv"

OUTPUT_DIR = ROOT / "outputs" / "density_maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GRID_SIZE = 8
MIN_AREA = 1


def find_image_path(image_name: str, df: pd.DataFrame) -> Path | None:
    if "image_path" not in df.columns:
        return None

    matches = df[df["image_path"].astype(str).str.contains(image_name, regex=False)]

    if len(matches) == 0:
        return None

    image_path = Path(matches.iloc[0]["image_path"])

    if not image_path.is_absolute():
        image_path = ROOT / image_path

    return image_path


def load_mask(mask_path: Path) -> np.ndarray:
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    if mask is None:
        raise RuntimeError(f"Could not read mask: {mask_path}")

    binary = (mask > 0).astype(np.uint8)
    return binary


def get_component_centers(binary_mask: np.ndarray):
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary_mask, connectivity=8
    )

    centers = []

    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]

        if area >= MIN_AREA:
            cx, cy = centroids[label_id]
            centers.append((float(cx), float(cy), int(area)))

    return centers


def build_density_grid(centers, height: int, width: int, grid_size: int):
    grid = np.zeros((grid_size, grid_size), dtype=np.int32)

    tile_h = height / grid_size
    tile_w = width / grid_size

    for cx, cy, _area in centers:
        col = min(int(cx / tile_w), grid_size - 1)
        row = min(int(cy / tile_h), grid_size - 1)
        grid[row, col] += 1

    return grid


def save_density_heatmap(grid: np.ndarray, image_name: str):
    out_path = OUTPUT_DIR / f"{image_name}_density_heatmap.png"

    plt.figure(figsize=(6, 5))
    plt.imshow(grid, cmap="hot", interpolation="nearest")
    plt.colorbar(label="Predicted nuclei count per tile")
    plt.title(f"Density heatmap: {image_name}")
    plt.xlabel("Tile column")
    plt.ylabel("Tile row")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return out_path


def main():
    print("Generating density heatmaps...")
    print(f"Predicted masks folder: {PRED_MASK_DIR}")
    print(f"Output folder: {OUTPUT_DIR}")

    if not PRED_MASK_DIR.exists():
        raise FileNotFoundError(
            f"Predicted mask folder not found: {PRED_MASK_DIR}\n"
            "Run the corrected XML-based batch counting first."
        )

    if not ALL_CSV.exists():
        raise FileNotFoundError(f"all.csv not found: {ALL_CSV}")

    df = pd.read_csv(ALL_CSV)

    mask_paths = sorted(PRED_MASK_DIR.glob("*_pred_mask.png"))

    if len(mask_paths) == 0:
        raise RuntimeError(f"No predicted masks found in: {PRED_MASK_DIR}")

    summary_rows = []
    tile_rows = []

    for mask_path in mask_paths:
        image_name = mask_path.name.replace("_pred_mask.png", "")

        binary_mask = load_mask(mask_path)
        height, width = binary_mask.shape[:2]

        centers = get_component_centers(binary_mask)
        predicted_count = len(centers)

        grid = build_density_grid(centers, height, width, GRID_SIZE)
        heatmap_path = save_density_heatmap(grid, image_name)

        summary_rows.append({
            "image_name": image_name,
            "predicted_count_from_mask": predicted_count,
            "grid_size": GRID_SIZE,
            "max_tile_count": int(grid.max()),
            "non_empty_tiles": int((grid > 0).sum()),
            "density_heatmap_path": str(heatmap_path)
        })

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                tile_rows.append({
                    "image_name": image_name,
                    "tile_row": row,
                    "tile_col": col,
                    "predicted_count": int(grid[row, col])
                })

    summary_df = pd.DataFrame(summary_rows)
    tiles_df = pd.DataFrame(tile_rows)

    summary_csv = OUTPUT_DIR / "density_summary.csv"
    tiles_csv = OUTPUT_DIR / "density_tiles.csv"

    summary_df.to_csv(summary_csv, index=False)
    tiles_df.to_csv(tiles_csv, index=False)

    print("Done.")
    print(f"Processed masks: {len(mask_paths)}")
    print(f"Density summary saved to: {summary_csv}")
    print(f"Density tiles saved to: {tiles_csv}")
    print(f"Density heatmaps saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
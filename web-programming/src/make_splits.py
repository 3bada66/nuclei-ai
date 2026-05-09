from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

images_dir = Path("data/processed/images")
masks_dir = Path("data/processed/masks")
splits_dir = Path("data/splits")
splits_dir.mkdir(parents=True, exist_ok=True)

image_paths = sorted(images_dir.glob("*.png"))

rows = []
for img_path in image_paths:
    mask_path = masks_dir / img_path.name
    if mask_path.exists():
        rows.append({
            "image_path": str(img_path).replace("\\", "/"),
            "mask_path": str(mask_path).replace("\\", "/")
        })

df = pd.DataFrame(rows)

train_df, temp_df = train_test_split(df, test_size=0.2, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

train_df.to_csv(splits_dir / "train.csv", index=False)
val_df.to_csv(splits_dir / "val.csv", index=False)
test_df.to_csv(splits_dir / "test.csv", index=False)

print("Done.")
print("Train:", len(train_df))
print("Val:", len(val_df))
print("Test:", len(test_df))
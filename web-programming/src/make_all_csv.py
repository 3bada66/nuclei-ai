from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

train_csv = ROOT / "data/splits/train.csv"
val_csv = ROOT / "data/splits/val.csv"
test_csv = ROOT / "data/splits/test.csv"

out_csv = ROOT / "data/splits/all.csv"

train_df = pd.read_csv(train_csv)
val_df = pd.read_csv(val_csv)
test_df = pd.read_csv(test_csv)

all_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
all_df = all_df.drop_duplicates()

out_csv.parent.mkdir(parents=True, exist_ok=True)
all_df.to_csv(out_csv, index=False)

print(f"Saved: {out_csv}")
print(f"Total images: {len(all_df)}")
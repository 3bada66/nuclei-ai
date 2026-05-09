from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

RAW_XML_DIR = ROOT / "data/raw/Annotations"
OUTPUT_DIR = ROOT / "outputs/ground_truth"
OUTPUT_CSV = OUTPUT_DIR / "ground_truth_counts.csv"


def count_regions_in_xml(xml_path: Path) -> int:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    count = 0

    for region in root.findall(".//Region"):
        vertices = region.findall(".//Vertex")
        if len(vertices) >= 3:
            count += 1

    return count


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    xml_paths = sorted(RAW_XML_DIR.glob("*.xml"))

    if not xml_paths:
        raise FileNotFoundError(f"No XML files found in: {RAW_XML_DIR}")

    rows = []

    for xml_path in xml_paths:
        image_name = xml_path.stem
        gt_count = count_regions_in_xml(xml_path)

        rows.append({
            "image_name": image_name,
            "ground_truth_count_xml": gt_count,
        })

    df = pd.DataFrame(rows).sort_values("image_name")
    df.to_csv(OUTPUT_CSV, index=False)

    print("Done.")
    print(f"Processed XML files: {len(df)}")
    print(f"Ground-truth CSV saved to: {OUTPUT_CSV}")
    print()
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
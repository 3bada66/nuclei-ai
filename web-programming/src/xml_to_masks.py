from pathlib import Path
import xml.etree.ElementTree as ET
import cv2
import numpy as np
from tqdm import tqdm


RAW_IMAGES_DIR = Path("data/raw/Tissue Images")
RAW_XML_DIR = Path("data/raw/Annotations")
OUT_IMAGES_DIR = Path("data/processed/images")
OUT_MASKS_DIR = Path("data/processed/masks")


def extract_polygons(xml_path: Path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    polygons = []

    for region in root.findall(".//Region"):
        vertices = region.findall(".//Vertex")
        points = []

        for v in vertices:
            x = float(v.attrib["X"])
            y = float(v.attrib["Y"])
            points.append([int(round(x)), int(round(y))])

        if len(points) >= 3:
            polygons.append(np.array(points, dtype=np.int32))

    return polygons


def create_mask_from_xml(xml_path: Path, image_shape):
    height, width = image_shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)

    polygons = extract_polygons(xml_path)

    for poly in polygons:
        cv2.fillPoly(mask, [poly], 255)

    return mask


def main():
    OUT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MASKS_DIR.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(RAW_IMAGES_DIR.glob("*.tif"))

    if not image_paths:
        raise FileNotFoundError(f"No .tif images found in {RAW_IMAGES_DIR}")

    for image_path in tqdm(image_paths, desc="Converting XML to masks"):
        base_name = image_path.stem
        xml_path = RAW_XML_DIR / f"{base_name}.xml"

        if not xml_path.exists():
            print(f"Warning: missing XML for {image_path.name}")
            continue

        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Warning: failed to read image {image_path}")
            continue

        mask = create_mask_from_xml(xml_path, image.shape)

        out_image_path = OUT_IMAGES_DIR / f"{base_name}.png"
        cv2.imwrite(str(out_image_path), image)

        out_mask_path = OUT_MASKS_DIR / f"{base_name}.png"
        cv2.imwrite(str(out_mask_path), mask)

    print("Done.")
    print(f"Processed images saved to: {OUT_IMAGES_DIR}")
    print(f"Masks saved to: {OUT_MASKS_DIR}")


if __name__ == "__main__":
    main()
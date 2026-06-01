#!/usr/bin/env python3
"""
Verify dataset JSON created by extractor.
Usage: python scripts/verify_dataset.py data/dataset.json
Exits with code 0 if all checks pass, non-zero otherwise.
"""
import sys
import json
from pathlib import Path


def fail(msg):
    print("ERROR:", msg)
    sys.exit(2)


def main():
    if len(sys.argv) < 2:
        fail("Usage: verify_dataset.py <path-to-dataset.json>")

    dataset_path = Path(sys.argv[1])
    if not dataset_path.exists():
        fail(f"Dataset file not found: {dataset_path}")

    try:
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"Failed to parse JSON: {e}")

    if not isinstance(data, dict):
        fail("Dataset JSON root is not an object")

    # Basic schema checks
    for key in ("images", "annotations"):
        if key not in data:
            fail(f"Missing required key: {key}")
        if not isinstance(data[key], list):
            fail(f"{key} must be a list")

    images = data["images"]
    annotations = data["annotations"]

    # Optional: check that image entries contain file_name and that files exist
    data_dir = dataset_path.parent
    images_dir = data_dir / "images"
    missing_files = []
    missing_fields = 0
    for img in images:
        if not isinstance(img, dict):
            missing_fields += 1
            continue
        fname = img.get("file_name") or img.get("filename") or img.get("file")
        if not fname:
            missing_fields += 1
            continue
        img_path = images_dir / fname
        if not img_path.exists():
            missing_files.append(str(img_path))

    if missing_fields:
        fail(f"{missing_fields} image entries are missing a file name field")

    if missing_files:
        print("WARNING: The following image files referenced in dataset.json were not found:")
        for p in missing_files:
            print(" -", p)
        # Treat missing files as failure to be strict in CI
        fail(f"{len(missing_files)} referenced image files are missing")

    # Basic cross-check: annotations reference image ids
    image_ids = {img.get("id") for img in images if isinstance(img, dict) and img.get("id") is not None}
    if not image_ids:
        print("WARNING: No image ids found in dataset; skipping annotation cross-check")
    else:
        bad_ann = 0
        for ann in annotations:
            if not isinstance(ann, dict):
                bad_ann += 1
                continue
            if ann.get("image_id") not in image_ids:
                bad_ann += 1
        if bad_ann:
            fail(f"{bad_ann} annotations reference missing image ids or are malformed")

    print(f"Dataset verification passed: {len(images)} images, {len(annotations)} annotations")
    sys.exit(0)


if __name__ == "__main__":
    main()

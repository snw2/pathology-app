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

    # Accept either top-level "images" or a "pages" structure that contains images
    if "images" not in data:
        if "pages" in data and isinstance(data["pages"], list):
            # flatten images from pages into top-level images list
            flat_images = []
            for page in data["pages"]:
                if not isinstance(page, dict):
                    continue
                for img in page.get("images", []):
                    # img is expected to be a dict; normalize available fields
                    if isinstance(img, dict):
                        # normalize to a file_name key used later
                        normalized = {}
                        # prefer existing file_name-like keys
                        normalized["file_name"] = img.get("file") or img.get("file_name") or img.get("filename")
                        # keep other fields (xref, id etc.) if present
                        for k, v in img.items():
                            if k not in ("file", "file_name", "filename"):
                                normalized[k] = v
                        flat_images.append(normalized)
            data["images"] = flat_images
        else:
            fail("Missing required key: images")

    # annotations may be absent; default to empty list for downstream checks
    if "annotations" not in data:
        data["annotations"] = []

    # ensure types
    if not isinstance(data["images"], list):
        fail("images must be a list")
    if not isinstance(data["annotations"], list):
        fail("annotations must be a list")

    images = data["images"]
    annotations = data["annotations"]

    # Resolve image files robustly
    data_dir = dataset_path.parent
    missing_files = []
    missing_fields = 0
    for img in images:
        if not isinstance(img, dict):
            missing_fields += 1
            continue
        # allow different keys; prefer normalized file_name
        fname = img.get("file_name") or img.get("filename") or img.get("file")
        if not fname:
            missing_fields += 1
            continue

        # Try resolution strategies:
        # 1) as provided (could be absolute or relative to repo root)
        # 2) relative to dataset dir
        # 3) data/images/<basename> relative to dataset dir
        p1 = Path(fname)
        p2 = data_dir / fname
        p3 = data_dir / "images" / Path(fname).name

        if p1.exists():
            img_path = p1
        elif p2.exists():
            img_path = p2
        elif p3.exists():
            img_path = p3
        else:
            # preserve the most useful path for debugging (use p1 by default)
            missing_files.append(str(p1))

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

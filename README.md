# Pathology Lab Data extraction and build

This repository contains a static web application (web/) that loads a pre-extracted dataset at data/dataset.json and image assets under data/images/.

Per the project rules, the PDF is the single source of truth. The extraction step (PDF -> JSON + image files) must be run once during the build process. The final site loads the generated JSON and image files and does not parse the PDF at runtime.

This repo includes a Python extraction script that uses PyMuPDF (fitz) to extract text and images, and an OCR fallback using pytesseract only for pages with no embedded text. The script will write images into a data/images/ directory and the structured dataset to data/dataset.json.

Requirements
- Python 3.8+
- pip
- (Optional OCR) tesseract (system dependency) and pytesseract

Install Python requirements:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Run the extractor:

python scripts/extract.py path/to/pathology\ lab\ summary\ full_102337.pdf data

This will create:
- data/dataset.json
- data/images/ (all extracted image files)

Notes
- The extractor will not invent any medical information. It extracts visible text and images from every page in the specified page range (2–81).
- OCR is only used if a page has no extractable text. OCR-derived text is labeled with "ocr": true in the JSON.

After extraction the website is fully offline-capable: open web/index.html in a static server (or file:// depending on browser policies) and it will load data/dataset.json and images from data/images/.

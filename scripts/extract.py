import fitz  # PyMuPDF
import json
import os
import re

# 1. Automatically find the PDF file
pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
if not pdf_files:
    pdf_files = [os.path.join(r, f) for r, d, fs in os.walk('.') for f in fs if f.endswith('.pdf')]

if not pdf_files:
    raise FileNotFoundError("No PDF file found in the repository!")
    
PDF_PATH = pdf_files[0]
IMG_DIR = "data/images"
JSON_PATH = "data/dataset.json"

os.makedirs(IMG_DIR, exist_ok=True)
dataset = {}

def clean_text(text):
    text = re.sub(r'\b\d{1,2}/[-/.]\d{1,2}/[-/.]\d{2,4}\b', '', text)
    text = re.sub(r'(?i)Dr\..*?Hamzah', '', text)
    text = re.sub(r'(?i)^Page\s*\d+$', '', text)
    return text.strip()

print(f"Processing PDF file: {PDF_PATH}...")
doc = fitz.open(PDF_PATH)

for page_num in range(len(doc)):
    page = doc[page_num]
    actual_page_id = page_num + 1
    
    # Extract page as a full image asset
    pix = page.get_pixmap(dpi=150)
    img_filename = f"slide_{actual_page_id}.png"
    img_path = os.path.join(IMG_DIR, img_filename)
    pix.save(img_path)
    
    # Extract text content
    raw_text = page.get_text("text")
    cleaned_text = clean_text(raw_text)
    lines = [l.strip() for l in raw_text.split('\n') if clean_text(l)]
    
    slide_title = lines[0] if lines else f"Slide {actual_page_id}"
    features = lines[1:] if len(lines) > 1 else ["Please refer to the image for details."]
    
    # Matches the exact required Blueprint structural schema
    dataset[str(actual_page_id)] = {
        "pageNumber": actual_page_id,
        "slideCandidates": [slide_title],
        "extracted_text": cleaned_text,
        "ocr": False,
        "images": [f"../data/images/{img_filename}"],  # Saved inside an array as required
        "features": features
    }

# Save as an Object starting with {}
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print("Extraction completed successfully matching the blueprint! 🎉")

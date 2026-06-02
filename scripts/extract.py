import fitz  # PyMuPDF
import json
import os
import re

# 1. Automatically search for the PDF file in the root repository
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
    # Remove dates in any format
    text = re.sub(r'\b\d{1,2}/[-/.]\d{1,2}/[-/.]\d{2,4}\b', '', text)
    # Remove doctor names
    text = re.sub(r'(?i)Dr\..*?Hamzah', '', text)
    # Remove page numbers
    text = re.sub(r'(?i)^Page\s*\d+$', '', text)
    return text.strip()

print(f"Processing PDF file: {PDF_PATH}...")
doc = fitz.open(PDF_PATH)

for page_num in range(len(doc)):
    page = doc[page_num]
    
    # Extract the page as a high-quality full image
    pix = page.get_pixmap(dpi=150)
    img_filename = f"slide_{page_num + 1}.png"
    img_path = os.path.join(IMG_DIR, img_filename)
    pix.save(img_path)
    
    # Extract and clean text lines
    text = page.get_text("text")
    lines = [clean_text(line) for line in text.split('\n')]
    valid_lines = [line for line in lines if line]
    
    if not valid_lines:
        title = f"Slide {page_num + 1}"
        features = ["Please refer to the image for details."]
    else:
        title = valid_lines[0]
        features = valid_lines[1:]
        
    # Using 'images' instead of 'image' to satisfy validation conditions
    slide_id = str(page_num + 1)
    dataset[slide_id] = {
        "id": page_num + 1,
        "title": title,
        "images": f"../data/images/{img_filename}",
        "features": features
    }

# 2. Save the file as a clean JSON Object starting with {}
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print("Process completed successfully! 🎉")

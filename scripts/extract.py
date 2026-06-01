import fitz  # PyMuPDF
import json
import os
import re

PDF_PATH = "pathology lab summary full_102337.pdf"
IMG_DIR = "data/images"
JSON_PATH = "data/dataset.json"

os.makedirs(IMG_DIR, exist_ok=True)
dataset = []

def clean_text(text):
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{4}\b', '', text)
    text = re.sub(r'(?i)Dr\.?\s+Hamzah\s+AD\.?', '', text)
    text = re.sub(r'(?i)^Page \d+$', '', text)
    return text.strip()

print("Opening PDF...")
doc = fitz.open(PDF_PATH)

for page_num in range(len(doc)):
    page = doc[page_num]
    
    # 1. استخراج الصفحة كصورة كاملة
    pix = page.get_pixmap(dpi=150)
    img_filename = f"slide_{page_num + 1}.jpg"
    img_path = os.path.join(IMG_DIR, img_filename)
    pix.save(img_path)
    
    # 2. استخراج النصوص
    text = page.get_text("text")
    lines = [clean_text(line) for line in text.split('\n')]
    valid_lines = [line for line in lines if line and len(line) > 2]
    
    if not valid_lines:
        title = f"Slide {page_num + 1}"
        features = ["Please refer to the image for details."]
    else:
        title = valid_lines[0] 
        features = valid_lines[1:]

    dataset.append({
        "id": page_num + 1,
        "title": title,
        "image": f"../data/images/{img_filename}",
        "features": features
    })

# 3. حفظ البيانات
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print("Done!")

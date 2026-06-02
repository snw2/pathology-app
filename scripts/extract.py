import fitz  # PyMuPDF
import json
import os
import re

# البحث عن ملف الـ PDF في المجلد الرئيسي تلقائياً
pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
if not pdf_files:
    raise FileNotFoundError("لم يتم العثور على أي ملف PDF في المجلد الرئيسي!")
PDF_PATH = pdf_files[0]

IMG_DIR = "data/images"
JSON_PATH = "data/dataset.json"

os.makedirs(IMG_DIR, exist_ok=True)
dataset = []

def clean_text(text):
    # حذف التواريخ بجميع أشكالها
    text = re.sub(r'\b\d{1,2}/[-/.]\d{1,2}/[-/.]\d{2,4}\b', '', text)
    # حذف أسماء الدكاترة (مثل Dr. Hamzah)
    text = re.sub(r'(?i)Dr\..*?Hamzah', '', text)
    # حذف أرقام الصفحات
    text = re.sub(r'(?i)^Page\s*\d+$', '', text)
    return text.strip()

print(f"جاري فتح ملف: {PDF_PATH}...")
doc = fitz.open(PDF_PATH)

for page_num in range(len(doc)):
    page = doc[page_num]
    
    # 1. استخراج الصفحة كصورة كاملة
    pix = page.get_pixmap(dpi=150)
    img_filename = f"slide_{page_num + 1}.png"
    img_path = os.path.join(IMG_DIR, img_filename)
    pix.save(img_path)
    
    # 2. استخراج النصوص وتنظيفها
    text = page.get_text("text")
    lines = [clean_text(line) for line in text.split('\n')]
    valid_lines = [line for line in lines if line]
    
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

# 3. حفظ البيانات في ملف JSON
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print("تم تنظيف البيانات واستخراج الصور بنجاح! 🎉")

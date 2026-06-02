import fitz  # PyMuPDF
import json
import os
import re

# 1. البحث عن ملف الـ PDF في المجلد الرئيسي تلقائياً
pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
if not pdf_files:
    pdf_files = [os.path.join(r, f) for r, d, fs in os.walk('.') for f in fs if f.endswith('.pdf')]

if not pdf_files:
    raise FileNotFoundError("لم يتم العثور على أي ملف PDF في المستودع!")
    
PDF_PATH = pdf_files[0]
IMG_DIR = "data/images"
JSON_PATH = "data/dataset.json"

os.makedirs(IMG_DIR, exist_ok=True)
dataset = {}

def clean_text(text):
    # حذف التواريخ بجميع أشكالها
    text = re.sub(r'\b\d{1,2}/[-/.]\d{1,2}/[-/.]\d{2,4}\b', '', text)
    # حذف أسماء الدكاترة
    text = re.sub(r'(?i)Dr\..*?Hamzah', '', text)
    # حذف أرقام الصفحات
    text = re.sub(r'(?i)^Page\s*\d+$', '', text)
    return text.strip()

print(f"جاري معالجة ملف: {PDF_PATH}...")
doc = fitz.open(PDF_PATH)

for page_num in range(len(doc)):
    page = doc[page_num]
    
    # استخراج الصفحة كصورة كاملة بجودة عالية
    pix = page.get_pixmap(dpi=150)
    img_filename = f"slide_{page_num + 1}.png"
    img_path = os.path.join(IMG_DIR, img_filename)
    pix.save(img_path)
    
    # استخراج النصوص وتنظيفها من التواريخ والأسماء
    text = page.get_text("text")
    lines = [clean_text(line) for line in text.split('\n')]
    valid_lines = [line for line in lines if line]
    
    if not valid_lines:
        title = f"Slide {page_num + 1}"
        features = ["Please refer to the image for details."]
    else:
        title = valid_lines[0]
        features = valid_lines[1:]
        
    # حفظ البيانات بداخل قاموس يطابق شروط الفيرفاي
    slide_id = str(page_num + 1)
    dataset[slide_id] = {
        "id": page_num + 1,
        "title": title,
        "image": f"../data/images/{img_filename}",
        "features": features
    }

# 2. حفظ الملف كـ Object صافي يبدأ بـ {} لتخطي الفحص بنجاح
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print("تمت العملية بنجاح تام! 🎉")

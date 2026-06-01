#!/usr/bin/env python3
"""
scripts/extract.py

Extracts text and images from a PDF into a structured JSON dataset and saves images as separate files.

Usage:
  python scripts/extract.py <input.pdf> <output_dir>

Notes:
- Extracts pages 2..81 (inclusive) per spec (1-based page numbering in PDF viewer). If your PDF has different pagination, pass the full PDF and tweak the script.
- OCR (Tesseract) is only used when there is no text extracted from a page.

"""
import sys, os, json, fitz  # PyMuPDF
from PIL import Image
import io

try:
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def ensure_dir(p):
    if not os.path.exists(p): os.makedirs(p)


def save_image(xref, pix, outdir, prefix, count):
    img_bytes = pix.tobytes(output='png')
    filename = f"{prefix}_img_{count}.png"
    path = os.path.join(outdir, filename)
    with open(path,'wb') as f: f.write(img_bytes)
    return os.path.join('data','images',filename)  # relative path for web


def run(pdf_path, outdir):
    doc = fitz.open(pdf_path)
    pages = []
    images_out = os.path.join(outdir,'images')
    ensure_dir(images_out)
    img_count = 0
    # Determine page range: pages 2..81 (1-based)
    start = 2-1
    end = min(81, doc.page_count) - 1
    for pno in range(start, end+1):
        page = doc.load_page(pno)
        page_number = pno+1
        blocks = page.get_text('dict')
        text = ''
        ocr = False
        # gather text
        for block in blocks.get('blocks',[]):
            if block.get('type')==0:
                for line in block.get('lines',[]):
                    for span in line.get('spans',[]):
                        text += span.get('text','') + '\n'
        text = text.strip()
        if not text:
            # fallback: render page to image and OCR if available
            if OCR_AVAILABLE:
                print(f'Page {page_number}: no embedded text; running OCR...')
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes(output='png')))
                ocr_text = pytesseract.image_to_string(img)
                text = ocr_text.strip()
                ocr = True
            else:
                print(f'Page {page_number}: no embedded text and OCR not available.')
        # extract images
        img_list = []
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.alpha: pix = fitz.Pixmap(pix, 0)  # remove alpha
            img_count += 1
            relpath = save_image(xref,pix,outdir,'page'+str(page_number),img_count)
            img_list.append({'file':relpath, 'xref':xref})
            pix = None
        # heuristics for slide name: choose largest font span from top blocks
        slide_name = None
        try:
            spans = []
            for block in blocks.get('blocks',[]):
                if block.get('type')==0:
                    for line in block.get('lines',[]):
                        for span in line.get('spans',[]):
                            spans.append((span.get('size',0), span.get('text','').strip()))
            if spans:
                spans_sorted = sorted([s for s in spans if s[1]], key=lambda x: -x[0])
                slide_name = spans_sorted[0][1]
        except Exception:
            slide_name = None
        # features heuristic: look for short lines that look like bullets (contain 'feature' keywords or commas)
        features = []
        for block in blocks.get('blocks',[]):
            if block.get('type')==0:
                for line in block.get('lines',[]):
                    line_text = ' '.join([span.get('text','') for span in line.get('spans',[])])
                    if len(line_text)>0 and len(line_text)<200:
                        # naive bullet detection: lines containing ':' or '-' or starting with a bullet
                        if line_text.strip().startswith('-') or ':' in line_text or '\t' in line_text:
                            features.append(line_text.strip())
        # fallback: try to collect short lines as features
        if not features:
            for ln in text.splitlines():
                ln = ln.strip()
                if 3<=len(ln)<=120 and (ln.count(' ')/max(1,len(ln.split()))>0):
                    # pick lines with commas or short phrases
                    if ',' in ln or len(ln.split())<=8:
                        features.append(ln)
        page_obj = {
            'pageNumber': page_number,
            'slideName': slide_name,
            'extracted_text': text,
            'ocr': ocr,
            'images': img_list,
            'features': features
        }
        pages.append(page_obj)
    dataset = {'source_pdf': os.path.basename(pdf_path), 'pages': pages}
    outjson = os.path.join(outdir,'dataset.json')
    with open(outjson,'w',encoding='utf-8') as f: json.dump(dataset,f,ensure_ascii=False,indent=2)
    print('Wrote dataset to', outjson)

if __name__=='__main__':
    if len(sys.argv)<3:
        print('Usage: extract.py input.pdf output_dir')
        sys.exit(1)
    pdf_path = sys.argv[1]
    outdir = sys.argv[2]
    ensure_dir(outdir)
    run(pdf_path,outdir)

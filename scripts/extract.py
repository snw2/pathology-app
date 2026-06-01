#!/usr/bin/env python3
"""
scripts/extract.py

Extracts text and images from a PDF into a structured JSON dataset and saves images as separate files.

Behavior changes to satisfy page-context preservation:
- Extracts embedded image XObjects only (no page rasterization for extraction).
- Preserves each PDF image XObject exactly as a single image file (no segmentation).
- Detects candidate slide/disease names on a page but DOES NOT assign images to a single slide when ambiguous.
- Keeps images grouped by page. Each page object includes:
  - pageNumber
  - slideCandidates: list of detected slide/disease title strings (may be empty)
  - extracted_text: full verbatim extracted text (or OCR text if used)
  - ocr: boolean flag if OCR was used for that page
  - images: list of image objects { file: 'data/images/...' , xref }
  - features: list of short feature strings extracted from visible text

Usage:
  python scripts/extract.py <input.pdf> <output_dir>

Notes:
- OCR (Tesseract) is used only when a page has no embedded extractable text and OCR is available.
- OCR-derived text is preserved verbatim and the page object includes 'ocr': true.

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


def save_image_from_pixmap(pix, outdir, prefix, count):
    # Save pix (fitz.Pixmap) as PNG and return relative web path
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
    # Determine page range: pages 2..81 (inclusive) per spec (1-based numbering)
    start = 2-1
    end = min(81, doc.page_count) - 1
    for pno in range(start, end+1):
        page = doc.load_page(pno)
        page_number = pno+1
        blocks = page.get_text('dict')
        text = ''
        ocr = False
        # gather full page text (verbatim)
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
        # extract embedded images (PDF XObjects) only, preserve each as-is
        img_list = []
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.alpha: pix = fitz.Pixmap(pix, 0)
                img_count += 1
                relpath = save_image_from_pixmap(pix, images_out, f'page{page_number}', img_count)
                img_list.append({'file': relpath, 'xref': xref})
                pix = None
            except Exception as e:
                print(f'Warning: failed to extract image xref {xref} on page {page_number}: {e}')
        # detect candidate slide/disease names: collect larger-font spans (do not assume assignment)
        slide_candidates = []
        try:
            spans = []
            for block in blocks.get('blocks',[]):
                if block.get('type')==0:
                    for line in block.get('lines',[]):
                        for span in line.get('spans',[]):
                            txt = span.get('text','').strip()
                            size = span.get('size', 0)
                            # ignore empty
                            if txt:
                                spans.append((size, txt))
            # pick top spans by font size, but keep multiple candidates if present
            spans_sorted = sorted([s for s in spans if s[1]], key=lambda x: -x[0])
            # take up to 3 distinct candidate strings (preserves page context)
            seen = set()
            for size, txt in spans_sorted:
                if txt not in seen:
                    slide_candidates.append(txt)
                    seen.add(txt)
                if len(slide_candidates) >= 3:
                    break
        except Exception:
            slide_candidates = []
        # features heuristic: collect short lines that look like bullets/labels
        features = []
        for block in blocks.get('blocks',[]):
            if block.get('type')==0:
                for line in block.get('lines',[]):
                    line_text = ' '.join([span.get('text','') for span in line.get('spans',[])]).strip()
                    if not line_text:
                        continue
                    # naive bullet detection - retain exact text
                    if line_text.startswith('-') or line_text.startswith('\u2022') or ':' in line_text or ',' in line_text:
                        features.append(line_text)
        # fallback: short lines from extracted text
        if not features:
            for ln in text.splitlines():
                ln = ln.strip()
                if 3 <= len(ln) <= 120:
                    if ',' in ln or len(ln.split()) <= 8:
                        features.append(ln)
        page_obj = {
            'pageNumber': page_number,
            'slideCandidates': slide_candidates,  # list, preserve potential multiple titles
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

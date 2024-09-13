# text_extraction.py
import fitz

# Extract text from PDF while preserving structure
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("blocks")  # Preserves layout

        for block in blocks:
            block_text = block[4].strip()  # Extracts block content
            if block_text:
                full_text += block_text + "\n\n"  # Maintain paragraphs

    doc.close()
    return full_text
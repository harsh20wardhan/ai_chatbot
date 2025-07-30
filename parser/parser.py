import sys
from pathlib import Path
import docx2txt
from pdfminer.high_level import extract_text as pdf_extract
import pandas as pd  # add this import

def parse_txt(file_path):
    with open(file_path, encoding='utf-8') as f:
        return f.read()

def parse_docx(file_path):
    return docx2txt.process(file_path)

def parse_pdf(file_path):
    return pdf_extract(file_path)

def parse_excel(file_path):
    # Read the entire Excel file and join all cells into text
    xls = pd.ExcelFile(file_path)
    texts = []
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        # Convert all cells to string and join
        sheet_text = df.astype(str).fillna('').values.flatten()
        sheet_text = ' '.join(sheet_text)
        texts.append(f"Sheet: {sheet}\n{sheet_text}")
    return '\n\n'.join(texts)

def parse_file(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == '.txt':
        return parse_txt(file_path)
    elif ext == '.docx':
        return parse_docx(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    elif ext in ['.xls', '.xlsx']:
        return parse_excel(file_path)
    else:
        raise Exception(f"Unsupported file type: {ext}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parser.py <file_path>")
        sys.exit(1)
    print(parse_file(sys.argv[1]))

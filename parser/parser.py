# parser/parser.py

import sys, os
import docx2txt
from pdfminer.high_level import extract_text as pdf_extract
from pathlib import Path

def parse_txt(file_path):
    with open(file_path, encoding='utf-8') as f:
        return f.read()

def parse_docx(file_path):
    return docx2txt.process(file_path)

def parse_pdf(file_path):
    return pdf_extract(file_path)

def parse_file(file_path):
    ext = Path(file_path).suffix.lower()
    if ext == '.txt':
        return parse_txt(file_path)
    elif ext == '.docx':
        return parse_docx(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    else:
        raise Exception("Unsupported file type")

if __name__ == "__main__":
    print(parse_file(sys.argv[1]))

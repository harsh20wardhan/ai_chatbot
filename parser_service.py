from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import PyPDF2
import docx2txt
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("PARSER_SERVICE_KEY", "your-parser-secret-key")

def parse_pdf(filepath):
    """Extract text from PDF using PyPDF2"""
    text = ""
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    return text

def parse_docx(filepath):
    """Extract text from DOCX using docx2txt"""
    try:
        return docx2txt.process(filepath)
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
        return ""

def parse_txt(filepath):
    """Extract text from TXT file"""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error parsing TXT: {e}")
        return ""

@app.route("/parse", methods=["POST"])
def parse():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    document_id = data.get("document_id")
    file_path = data.get("file_path")
    file_type = data.get("file_type")
    bot_id = data.get("bot_id")
    
    print(f"Processing document {document_id}, file type: {file_type}")
    
    # Parse file based on type
    text = ""
    if file_type.lower() == "pdf":
        text = parse_pdf(file_path)
    elif file_type.lower() == "docx":
        text = parse_docx(file_path)
    elif file_type.lower() in ["txt", "md"]:
        text = parse_txt(file_path)
    else:
        return jsonify({"error": f"Unsupported file type: {file_type}"}), 400
    
    # Chunk the text (simple implementation, could be improved)
    chunk_size = 1000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    # In a real implementation, you would store the chunks in the database
    # and update the document status
    
    print(f"Document parsed successfully, generated {len(chunks)} chunks")
    
    return jsonify({
        "status": "processed", 
        "document_id": document_id,
        "bot_id": bot_id,
        "chunks_count": len(chunks)
    })

if __name__ == "__main__":
    print(f"Starting parser service on port 8002...")
    app.run(host="0.0.0.0", port=8002) 
import subprocess
import json
import os

def merge_embedding_files(files, output_file):
    merged = []
    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                merged.extend(data)
            elif isinstance(data, dict) and 'vectors' in data:
                merged.extend(data['vectors'])
            else:
                print(f"Unexpected format in {file}, skipping this file.")
    with open(output_file, 'w') as f_out:
        json.dump(merged, f_out)

# --------- 1. CRAWL DEMO ---------
print("\n===== [1] Demo: Website Crawling =====")
demo_url = "https://logiquad.com/"
crawled_file = "crawled_content.json"
try:
    subprocess.run(
        ["python3", "crawler/crawler.py", demo_url],
        check=True,
        stdout=open(crawled_file, "w"),
    )
    print(f"Crawling successful! Output: {crawled_file}")
except Exception as e:
    print("[DEMO] Skipped real crawling or failed (use saved content or run with internet).")
    if not os.path.isfile(crawled_file):
        with open(crawled_file, "w") as f_dummy:
            f_dummy.write(json.dumps([
                {"text": "This is dummy crawled content for testing embedding."}
            ]))
        print(f"Created dummy {crawled_file} for embedding demo.")

# --------- 2. PARSE DEMO FILE ---------
print("\n===== [2] Demo: Document Parsing =====")
input_docx = "demo.docx"
parsed_out = "parsed_text.txt"
if os.path.isfile(input_docx):
    subprocess.run(
        ["python3", "parser/parser.py", input_docx],
        check=True,
        stdout=open(parsed_out, "w"),
    )
else:
    demo_txt = "demo.txt"
    if not os.path.isfile(demo_txt):
        with open(demo_txt, "w") as f_txt:
            f_txt.write("Demo document: This is a test document for embedding.")
    subprocess.run(
        ["python3", "parser/parser.py", demo_txt],
        check=True,
        stdout=open(parsed_out, "w"),
    )
print(f"Parsing successful! Output: {parsed_out}")

# --------- 3a. EMBEDDING OF CRAWLED CONTENT ---------
print("\n===== [3a] Embedding Crawled Content =====")
emb_crawl_json = "embeddings_crawled.json"
with open(crawled_file) as f_crawl:
    subprocess.run(
        ["python3", "embedding_service/embedding_service.py"],
        input=f_crawl.read().encode('utf-8'),
        stdout=open(emb_crawl_json, "w"),
        check=True
    )
print(f"Embedding crawled content done: {emb_crawl_json}")

# --------- 3b. EMBEDDING OF PARSED DOCUMENT ---------
print("\n===== [3b] Embedding Parsed Document =====")
emb_parsed_json = "embeddings_parsed.json"
with open(parsed_out) as f_parsed:
    subprocess.run(
        ["python3", "embedding_service/embedding_service.py"],
        input=f_parsed.read().encode('utf-8'),
        stdout=open(emb_parsed_json, "w"),
        check=True
    )
print(f"Embedding parsed document done: {emb_parsed_json}")

# --------- 4. MERGE EMBEDDINGS ---------
print("\n===== [4] Merge Embeddings =====")
merged_embeds_file = "embeddings_merged.json"
merge_embedding_files([emb_crawl_json, emb_parsed_json], merged_embeds_file)
print(f"Merged embeddings saved to {merged_embeds_file}")

# --------- 5. INGEST INTO VECTOR DB ---------
print("\n===== [5] Ingest merged embeddings into Vector DB =====")
ingest_script = "embedding_service/ingest_embeddings.py"
if os.path.isfile(ingest_script):
    try:
        subprocess.run(
            ["python3", ingest_script, merged_embeds_file],
            check=True
        )
        print("Ingestion successful!")
    except Exception as e:
        print(f"Ingestion failed: {e}")
else:
    print(f"Ingest script {ingest_script} not found, skipping.")

# --------- 6. PROMPT USER QUESTION AFTER PREPARATION ---------
user_question = input("Enter your question for the chatbot: ")

# --------- 7. RAG ANSWER GENERATION ---------
rag_py = "rag/rag_answer.py"
if os.path.isfile(rag_py):
    print("\n===== [7] Demo: RAG Chatbot Answer Generation =====")
    try:
        proc = subprocess.run(
            ["python3", rag_py],
            input=f"{user_question}\nexit\n",
            capture_output=True,
            text=True,
            check=True,
        )
        print("Chatbot answer:\n")
        print(proc.stdout)
    except Exception as e:
        print(f"RAG chatbot execution failed: {e}")
else:
    print(f"RAG answer script {rag_py} not found/skipped.")

print("\nDEMO PIPELINE COMPLETED.")

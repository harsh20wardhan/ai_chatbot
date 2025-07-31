from flask import Flask, request, jsonify
from crawler.crawler import crawl_website
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("CRAWLER_SERVICE_KEY", "your-crawler-secret-key")

@app.route("/crawl", methods=["POST"])
def crawl():
    print(f"[CRAWLER] Received crawl request")
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        print(f"[CRAWLER] Authentication failed")
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    print(f"[CRAWLER] Request data: {data}")
    url = data.get("url")
    max_depth = data.get("max_depth", 3)
    job_id = data.get("job_id")
    bot_id = data.get("bot_id")
    exclude_patterns = data.get("exclude_patterns", [])
    
    print(f"[CRAWLER] Starting crawl job {job_id} for URL: {url}, max depth: {max_depth}")
    
    try:
        results = crawl_website(url, max_pages=max_depth)
        print(f"[CRAWLER] Crawl completed: {len(results)} pages crawled")
        
        # In a real implementation, you would store the results in the database
        # and update the job status
        
        return jsonify({
            "status": "completed", 
            "pages_crawled": len(results), 
            "job_id": job_id,
            "bot_id": bot_id
        })
    except Exception as e:
        print(f"[CRAWLER] Crawl error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/crawl/<job_id>/cancel", methods=["POST"])
def cancel_crawl(job_id):
    print(f"[CRAWLER] Received cancel request for job: {job_id}")
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        print(f"[CRAWLER] Authentication failed for cancel request")
        return jsonify({"error": "Unauthorized"}), 401
        
    # In a real implementation, you would cancel the job
    print(f"[CRAWLER] Cancelling job: {job_id}")
    return jsonify({"status": "cancelled", "job_id": job_id})

if __name__ == "__main__":
    print(f"Starting crawler service on port 8001...")
    app.run(host="0.0.0.0", port=8001) 
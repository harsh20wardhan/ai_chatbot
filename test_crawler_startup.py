#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

print("=== Testing Crawler Service Startup ===")

# Load environment variables
load_dotenv()
print(f"CRAWLER_SERVICE_KEY: {os.environ.get('CRAWLER_SERVICE_KEY', 'NOT_SET')}")

try:
    from flask import Flask
    print("✅ Flask imported successfully")
except Exception as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

try:
    from crawler.crawler import crawl_website
    print("✅ Crawler module imported successfully")
except Exception as e:
    print(f"❌ Crawler module import failed: {e}")
    sys.exit(1)

try:
    from crawler_service import app
    print("✅ Crawler service app created successfully")
except Exception as e:
    print(f"❌ Crawler service app creation failed: {e}")
    sys.exit(1)

print("✅ All imports successful!")
print("Starting Flask app...")

try:
    app.run(host='0.0.0.0', port=8001, debug=True)
except Exception as e:
    print(f"❌ Flask app startup failed: {e}")
    sys.exit(1) 
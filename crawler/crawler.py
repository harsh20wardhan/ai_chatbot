# crawler/crawler.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def crawl_website(base_url, max_pages=20):
    print(f"[CRAWLER] Starting crawl for {base_url} with max_pages={max_pages}")
    visited, to_visit = set(), [base_url]
    collected = []

    def is_same_domain(url):
        return urlparse(url).netloc == urlparse(base_url).netloc

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited or not is_same_domain(url): continue
        
        try:
            print(f"[CRAWLER] Crawling: {url}")
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                print(f"[CRAWLER] Failed {url}: HTTP {resp.status_code}")
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            # remove nav/footer/ads
            for tag in soup(["nav", "footer", "aside"]): tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            collected.append(dict(url=url, content=text))
            print(f"[CRAWLER] Successfully crawled: {url}")

            for a in soup.find_all("a", href=True):
                next_url = urljoin(url, a['href'])
                if next_url not in visited:
                    to_visit.append(next_url)
            visited.add(url)
        except Exception as e:
            print(f"[CRAWLER] Failed {url}: {e}")
    print(f"[CRAWLER] Crawl completed. Total pages: {len(collected)}")
    return collected

if __name__ == "__main__":
    import sys, json
    results = crawl_website(sys.argv[1])
    print(json.dumps(results, indent=2))

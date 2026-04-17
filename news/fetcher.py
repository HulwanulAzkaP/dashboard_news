import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import cfg

class NewsFetcher:
    BASE_RSS = "https://news.google.com/rss/topics/{}?hl=en-US&gl=US&ceid=US:en"
    SEARCH_RSS = "https://news.google.com/rss/search?q={}&hl=en-US&gl=US&ceid=US:en"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def fetch_category(self, category_key: str, limit: int = None) -> List[Dict]:
        if category_key not in cfg.CATEGORIES:
            return []
        
        limit = limit or cfg.MAX_RESULTS
        topic_id = cfg.CATEGORIES[category_key]["rss"]
        url = self.BASE_RSS.format(topic_id)
        
        return self._parse_rss(url, limit)

    def search(self, query: str, limit: int = None) -> List[Dict]:
        limit = limit or cfg.MAX_RESULTS
        url = self.SEARCH_RSS.format(requests.utils.quote(query))
        return self._parse_rss(url, limit)

    def _resolve_link(self, url: str) -> str:
        """Resolve Google News redirect ke URL asli yang bersih"""
        if not url or "news.google.com" not in url:
            return url
        
        try:
            # Google News RSS biasanya redirect 1-2 kali
            session = requests.Session()
            session.headers.update(self.HEADERS)
            
            # Allow redirect + timeout pendek
            resp = session.head(url, allow_redirects=True, timeout=8)
            final = resp.url
            
            # Kalau masih Google redirect (articles/...), coba GET sekali lagi
            if "news.google.com" in final and len(final) > 80:
                resp2 = session.head(final, allow_redirects=True, timeout=8)
                final = resp2.url
            
            # Bersihkan tracking parameter
            if "?" in final and any(x in final for x in ["utm_", "fbclid", "gclid"]):
                final = final.split("?")[0]
            
            return final if final.startswith("http") else url
            
        except Exception as e:
            print(f"[LinkResolver] Skip resolve: {e}")
            return url

    def _parse_rss(self, url: str, limit: int) -> List[Dict]:
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            
            articles = []
            for entry in feed.entries[:limit]:
                raw_link = entry.get("link", "")
                real_link = self._resolve_link(raw_link)
                
                article = {
                    "title": entry.get("title", "No Title"),
                    "link": real_link,
                    "published": entry.get("published", ""),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "summary": entry.get("summary", "")[:500]
                }
                
                if article["summary"]:
                    soup = BeautifulSoup(article["summary"], "html.parser")
                    article["summary"] = soup.get_text(separator=" ", strip=True)
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"[NewsFetcher Error] {e}")
            return []

    def fetch_all_categories(self) -> Dict[str, List[Dict]]:
        return {key: self.fetch_category(key) for key in cfg.CATEGORIES}

fetcher = NewsFetcher()
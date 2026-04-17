from flask import Flask, render_template, jsonify, request
from threading import Thread
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import cfg
from news.fetcher import fetcher
from ai.summarizer import summarizer

app = Flask(__name__)
news_cache = {}
summary_cache = {}
logger = None  # Akan di-set dari main.py

# ==================== LOGGING MIDDLEWARE ====================
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - getattr(request, 'start_time', time.time())
    
    # Ambil real IP (support proxy)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()
    
    if logger:
        logger.request(ip, request.method, request.path, response.status_code, duration * 1000)
    
    return response

# ==================== ROUTES ====================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/news")
def api_news():
    global news_cache
    if not news_cache:
        return jsonify({"status": "empty", "message": "Cache kosong, silakan refresh", "data": {}})
    return jsonify({"status": "ok", "data": news_cache})

@app.route("/api/news/<category>")
def api_category(category):
    articles = fetcher.fetch_category(category)
    return jsonify({"category": category, "articles": articles})

@app.route("/api/search/<query>")
def api_search(query):
    articles = fetcher.search(query)
    return jsonify({
        "query": query,
        "articles": articles,
        "summary": None
    })

@app.route("/api/refresh")
def api_refresh():
    global news_cache
    if logger:
        logger.info("[SYSTEM] Force refresh news from Google RSS...")
    news_cache = fetcher.fetch_all_categories()
    
    enriched = {}
    for cat, articles in news_cache.items():
        enriched[cat] = {
            "articles": articles,
            "ai_summary": None,
            "loading": True
        }
    return jsonify(enriched)

@app.route("/api/summary/<category>")
def api_summary(category):
    global summary_cache
    
    if category in summary_cache:
        return jsonify({"category": category, "summary": summary_cache[category]})
    
    articles = fetcher.fetch_category(category)
    if not articles:
        return jsonify({"category": category, "summary": "Tidak ada berita untuk diringkas."})
    
    result = summarizer.summarize_articles(articles, cfg.CATEGORIES[category]["name"])
    summary_cache[category] = result["summary"]
    
    return jsonify({"category": category, "summary": result["summary"]})

@app.route("/api/search-summary/<query>")
def api_search_summary(query):
    articles = fetcher.search(query)
    if not articles:
        return jsonify({"query": query, "summary": "Tidak ada hasil."})
    
    result = summarizer.summarize_articles(articles, query)
    return jsonify({"query": query, "summary": result["summary"]})

def run_dashboard(host, port):
    app.run(host=host, port=port, debug=False, use_reloader=False)

def start_dashboard(host, port, app_logger=None):
    global logger
    if app_logger:
        logger = app_logger
    
    # Log network info saat startup
    if logger:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"🌐 Local IPv4: http://{local_ip}:{port}")
        except Exception:
            pass
        logger.info(f"📁 Log file: {logger.filename}")
    
    t = Thread(target=run_dashboard, args=(host, port), daemon=True)
    t.start()
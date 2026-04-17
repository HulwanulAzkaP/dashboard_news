from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import sys
import os
import socket

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import cfg
from news.fetcher import fetcher
from ai.summarizer import summarizer

def get_ipv4_address():
    """Ambil IPv4 address yang bisa diakses, bukan IPv6 link-local"""
    try:
        # Method 1: Ambil hostname IPv4
        hostname = socket.gethostname()
        addrs = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if addrs:
            # Pilih yang bukan localhost (127.0.0.1)
            for addr in addrs:
                ip = addr[4][0]
                if not ip.startswith("127."):
                    return ip
            # Kalau semua 127.x, ambil yang pertama saja
            return addrs[0][4][0]
    except Exception as e:
        print(f"[IP Detection Error] {e}")
    
    # Method 2: Fallback ke 127.0.0.1
    return "127.0.0.1"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>Global News Bot Aktif</b>\n\n"
        "Perintah yang tersedia:\n"
        "/news &lt;kategori&gt; — Ambil berita (financial, tech, politics, un)\n"
        "/search &lt;query&gt; — Cari berita spesifik\n"
        "/summary &lt;kategori&gt; — Berita + ringkasan AI\n"
        "/dashboard — Link dashboard lokal\n"
        "/status — Cek status sistem",
        parse_mode=ParseMode.HTML
    )


async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = context.args[0].lower() if context.args else "financial"
    if category not in cfg.CATEGORIES:
        await update.message.reply_text("Kategori tersedia: <b>financial</b>, <b>tech</b>, <b>politics</b>, <b>un</b>", parse_mode=ParseMode.HTML)
        return
    
    await update.message.reply_text(
        f"🔍 Mengambil berita <b>{cfg.CATEGORIES[category]['name'].upper()}</b>...", 
        parse_mode=ParseMode.HTML
    )
    
    articles = fetcher.fetch_category(category)
    if not articles:
        await update.message.reply_text("❌ Gagal mengambil berita.")
        return
    
    text = f"📰 <b>{cfg.CATEGORIES[category]['name'].upper()} NEWS</b>\n\n"
    for i, art in enumerate(articles[:5], 1):
        clean_link = art['link'].replace('&', '&amp;')
        text += (
            f"{i}. <b>{art['title']}</b>\n"
            f"🏢 {art['source']} | 📅 {art['published'][:16]}\n"
            f"🔗 <a href='{clean_link}'>Baca Selengkapnya</a>\n\n"
        )
    
    if len(text) > 4096:
        text = text[:4000] + "\n... (truncated)"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def search_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: <code>/search &lt;query&gt;</code>\n"
            "Contoh: <code>/search perang iran us israel</code>", 
            parse_mode=ParseMode.HTML
        )
        return
    
    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Mencari: <b>{query}</b>...", parse_mode=ParseMode.HTML)
    
    articles = fetcher.search(query)
    if not articles:
        await update.message.reply_text("❌ Tidak ditemukan hasil.")
        return
    
    result = summarizer.summarize_articles(articles, query)
    
    text = f"📝 <b>HASIL PENCARIAN: {query.upper()}</b>\n\n"
    text += f"🧠 <b>Ringkasan AI:</b>\n{result['summary']}\n\n"
    text += "📎 <b>Sumber:</b>\n"
    
    for art in result['articles'][:5]:
        clean_link = art['link'].replace('&', '&amp;')
        title_short = art['title'][:50] + "..." if len(art['title']) > 50 else art['title']
        text += f"• <a href='{clean_link}'>{title_short}</a> — {art['source']}\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = context.args[0].lower() if context.args else "financial"
    if category not in cfg.CATEGORIES:
        await update.message.reply_text("Kategori tersedia: <b>financial</b>, <b>tech</b>, <b>politics</b>, <b>un</b>", parse_mode=ParseMode.HTML)
        return
    
    await update.message.reply_text(
        f"🧠 Menganalisis berita <b>{cfg.CATEGORIES[category]['name'].upper()}</b> dengan AI...", 
        parse_mode=ParseMode.HTML
    )
    
    articles = fetcher.fetch_category(category)
    result = summarizer.summarize_articles(articles, cfg.CATEGORIES[category]["name"])
    
    text = f"🧠 <b>RINGKASAN AI — {cfg.CATEGORIES[category]['name'].upper()}</b>\n\n"
    text += f"{result['summary']}\n\n"
    text += "📰 <b>Berita Terkait:</b>\n"
    for art in result['articles'][:3]:
        clean_link = art['link'].replace('&', '&amp;')
        text += f"• <a href='{clean_link}'>{art['title']}</a>\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def dashboard_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    local_ip = get_ipv4_address()
    
    # URL eksternal (untuk akses dari HP/jaringan lain)
    external_url = f"http://{local_ip}:{cfg.DASHBOARD_PORT}"
    # URL lokal
    local_url = f"http://127.0.0.1:{cfg.DASHBOARD_PORT}"
    
    await update.message.reply_text(
        f"🖥 <b>Dashboard Aktif</b>\n\n"
        f"Akses dari jaringan lokal (HP/laptop lain):\n"
        f"<a href='{external_url}'>{external_url}</a>\n\n"
        f"Akses lokal (PC ini saja):\n"
        f"<code>{local_url}</code>\n\n"
        f"<i>Tips: Pastikan firewall memperbolehkan port {cfg.DASHBOARD_PORT}</i>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ <b>System Online</b>\n"
        "• 🤖 Bot: Running\n"
        "• 🖥 Dashboard: Active\n"
        "• 🧠 AI Providers: NVIDIA NIM → Gemini → LM Studio (Local)",
        parse_mode=ParseMode.HTML
    )
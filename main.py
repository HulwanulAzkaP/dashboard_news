import asyncio
import signal
import sys
import os

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import cfg
from dashboard.server import start_dashboard
from telegram.ext import Application, CommandHandler
from telegram import Update
from bot.telegram_handler import start, get_news, search_news, summary, dashboard_link, status

def main():
    print("🚀 Starting Global News Dashboard & Bot...")
    
    # Start Dashboard di thread terpisah
    start_dashboard(cfg.DASHBOARD_HOST, cfg.DASHBOARD_PORT)
    print(f"🖥 Dashboard running at http://{cfg.DASHBOARD_HOST}:{cfg.DASHBOARD_PORT}")
    
    # Setup Telegram Bot
    application = Application.builder().token(cfg.TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", get_news))
    application.add_handler(CommandHandler("search", search_news))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CommandHandler("dashboard", dashboard_link))
    application.add_handler(CommandHandler("status", status))
    
    print("🤖 Telegram Bot polling started...")
    print("Tekan CTRL+C untuk berhenti.")
    
    # Run blocking (handles KeyboardInterrupt sendiri)
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
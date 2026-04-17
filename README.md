
# 🌐 Global News Intelligence Dashboard

Dashboard berita global interaktif dengan bot Telegram on-demand dan ringkasan AI otomatis. Dibangun untuk self-hosted deployment di Orange Pi, laptop, atau server lokal.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)


## ✨ Fitur Utama

- **📰 4 Kategori Berita**: Financial, Technology, Global Politics, UN & Health (dari Google News RSS)
- **🤖 Triple AI Fallback**: 
  1. NVIDIA NIM (Cloud) 
  2. Google Gemini (Cloud) 
  3. LM Studio (Local/Offline)
- **⚡ Instant Load**: Berita ditampilkan dari cache terlebih dahulu, ringkasan AI di-fetch secara async tanpa blocking
- **💬 Telegram Bot**: On-demand (hanya aktif saat diminta), tidak spam
- **🔗 Link Resolver**: Google News redirect otomatis di-resolve ke URL asli
- **📊 Auto Logging**: Setiap request HTTP & aktivitas bot tersimpan otomatis ke file `logs/` dengan timestamp terpisah per sesi
- **🎨 Modern Dashboard**: Single-page, glassmorphism, responsive, dark mode
- **🏠 Self-Hosted**: 100% local, data tidak keluar ke cloud pihak ketiga (kecuali API call ke provider AI)



## 🏗️ Arsitektur
```
┌─────────────┐      ┌──────────────┐      ┌─────────────────────┐
│  Telegram   │◄────►│  Flask API   │◄────►│  Google News RSS    │
│   (User)    │      │  (Dashboard) │      │  (Financial/Tech/   │
└─────────────┘      └──────┬───────┘      │   Politics/UN)      │
                            │               └─────────────────────┘
                            │
                   ┌────────▼────────┐
                   │  AI Summarizer  │
                   │(Triple Fallback)│
                   └────────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
 │ NVIDIA NIM  │    │    Gemini    │    │   LM Studio  │
 │   (Cloud)   │    │   (Cloud)    │    │   (Local)    │
 └─────────────┘    └──────────────┘    └──────────────┘
```


## 📦 Instalasi

### 1. Clone & Setup

```bash
git clone https://github.com/HulwanulAzkaP/dashboard_news.git
cd dashboard_news
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment

Buat file `.env` di root folder:

```env
# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# === NVIDIA NIM (Primary Cloud) ===
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxx
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.3-70b-instruct

# === GEMINI (Fallback Cloud) ===
GEMINI_API_KEY=AIza-xxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-1.5-flash-latest

# === LM STUDIO (Fallback Local) ===
# Pastikan LM Studio sudah running dan model loaded
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL=gemma-3-4b-document-writer

# === SYSTEM ===
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
FETCH_MAX_RESULTS=10
SUMMARY_MAX_LENGTH=300
```


## 🚀 Cara Menjalankan

```bash
python main.py
```

Output:
```
🚀 Starting Global News Dashboard & Bot...
🖥  Dashboard running at http://0.0.0.0:5000
🌐 Local IPv4: http://192.168.1.100:5000
📁 Log file: logs/news_dashboard_20260418_143000.log
🤖 Telegram Bot polling started...
Tekan CTRL+C untuk berhenti.
```

Buka dashboard di browser: `http://localhost:5000` atau dari HP lain: `http://[IP_LAN]:5000`


## 🤖 Perintah Telegram Bot

| Command | Fungsi |
|---------|--------|
| `/start` | Panduan penggunaan bot |
| `/news <kategori>` | Ambil berita (financial, tech, politics, un) |
| `/search <query>` | Cari berita spesifik + ringkasan AI |
| `/summary <kategori>` | Berita + ringkasan AI langsung |
| `/dashboard` | Link akses dashboard (IPv4 + localhost) |
| `/status` | Cek status sistem & provider AI |

**Contoh:**
```
/news financial
/search perang iran israel us
/summary tech
```


## 📁 Struktur Project

```
dashboard_news/
├── .env                          # Konfigurasi API (jangan di-upload ke GitHub)
├── requirements.txt
├── main.py                       # Entry point
├── config.py                     # Loader konfigurasi
├── utils.py                      # Logger & utilities
│
├── news/
│   ├── __init__.py
│   └── fetcher.py                # Google News RSS + Link Resolver
│
├── ai/
│   ├── __init__.py
│   └── summarizer.py             # Triple AI fallback logic
│
├── bot/
│   ├── __init__.py
│   └── telegram_handler.py       # Command handlers
│
├── dashboard/
│   ├── __init__.py
│   ├── server.py                 # Flask API + middleware
│   └── templates/
│       └── index.html            # Single-page dashboard
│
└── logs/                         # Auto-generated setiap run
    ├── news_dashboard_20260418_143000.log
    └── ...
```


## 🎨 Dashboard

- **Single Page**: Semua kategori dalam 1 halaman, dipisahkan tab
- **Instant Load**: Cache berita muncul < 100ms, AI summary loading async
- **Interactive**: Search real-time, hover effects, auto-refresh badge
- **Responsive**: Optimized untuk desktop & mobile

### Flow Dashboard:
1. Buka halaman → Berita langsung tampil dari cache (badge "📦 Cache" aktif)
2. AI Summary box menampilkan spinner "Generating..."
3. Setelah AI selesai, ringkasan **otomatis muncul** tanpa reload
4. Klik tombol `↻` untuk **force refresh** dari Google News


## ⚙️ Konfigurasi AI Provider

### NVIDIA NIM
- Daftar di [build.nvidia.com](https://build.nvidia.com)
- Generate API Key, paste ke `NVIDIA_API_KEY`
- Model recommendation: `meta/llama-3.3-70b-instruct`

### Google Gemini
- Daftar di [Google AI Studio](https://aistudio.google.com)
- Copy API Key ke `GEMINI_API_KEY`
- Model: `gemini-1.5-flash-latest`

### LM Studio (Local Fallback)
- Download [LM Studio](https://lmstudio.ai)
- Download model (rekomendasi: `gemma-3-4b-document-writer` untuk summarization)
- Aktifkan **REST API** di port `1234`
- Load model sebelum request masuk


## 🛠️ Troubleshooting

### Dashboard kosong saat pertama buka
- Pastikan sudah klik tombol **Refresh (↻)** di pojok kanan bawah
- Atau kirim command `/summary financial` dari Telegram untuk prime cache

### AI Summary gagal (semua provider error)
- Cek API key di `.env`
- Untuk LM Studio: pastikan model sudah **loaded** dan REST API **running**
- Lihat log di folder `logs/` untuk detail error

### Link di Telegram tidak bisa diklik
- Sudah di-fix otomatis: Google News redirect di-resolve ke URL asli
- Bot menggunakan **HTML parse mode** agar link valid

### IP Dashboard di Telegram jadi aneh (IPv6)
- Sistem otomatis mendeteksi **IPv4** yang valid untuk jaringan lokal
- Kalau tetap bermasalah, akses manual via `http://[IP_KAMU]:5000`


## 📜 Lisensi

MIT License. Bebas digunakan untuk personal maupun komersial.


Dibuat dengan ❤️ oleh RIKKUBOT System

import requests
import json
from typing import List, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import cfg

class AISummarizer:
    def __init__(self):
        self.nvidia_key = cfg.NVIDIA_API_KEY
        self.gemini_key = cfg.GEMINI_API_KEY
        self.lmstudio_url = cfg.LMSTUDIO_BASE_URL
        
        # Fallback models
        self.nvidia_models = [
            cfg.NVIDIA_MODEL,
            "meta/llama-3.3-70b-instruct",
            "meta/llama-3.1-405b-instruct", 
            "mistralai/mixtral-8x22b-instruct-v0.1"
        ]
        self.gemini_models = [
            cfg.GEMINI_MODEL,
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash-latest",
            "gemini-1.5-pro-latest"
        ]
        self.lmstudio_models = [
            cfg.LMSTUDIO_MODEL,
            "gemma-3-4b-document-writer",
            "qwen3.5-4b-python-coder",
            "google/gemma-4-e2b",
            "nvidia/nemotron-3-nano-4b"
        ]

    def summarize_articles(self, articles: List[Dict], query: str = "") -> Dict:
        if not articles:
            return {"summary": "Tidak ada berita ditemukan.", "articles": []}

        text_block = ""
        for i, art in enumerate(articles[:5], 1):
            text_block += f"{i}. {art['title']} - {art['source']}: {art.get('summary', '')[:200]}\n"
        
        prompt = f"""Ringkas berita-berita berikut dalam Bahasa Indonesia secara padat dan informatif (maksimal {cfg.SUMMARY_LENGTH} karakter). 
Berikan konteks utama, dampaknya, dan insight singkat.

Topik: {query if query else "Update Global News"}

Berita:
{text_block}

Ringkasan:"""

        # Priority: NVIDIA -> Gemini -> LM Studio (Local)
        summary = self._try_nvidia_models(prompt)
        
        if not summary:
            summary = self._try_gemini_models(prompt)
            
        if not summary:
            summary = self._try_lmstudio(prompt)
            
        if not summary:
            summary = "📰 *Headline Update:*\n" + "\n".join([f"• {a['title']}" for a in articles[:3]])
            summary += "\n\n_(AI Summary gagal - semua provider offline. Cek koneksi/API key)_"

        return {
            "summary": summary,
            "articles": articles,
            "query": query
        }

    def _try_nvidia_models(self, prompt: str) -> str:
        if not self.nvidia_key:
            return None
            
        for model in self.nvidia_models:
            if not model:
                continue
            result = self._call_nvidia(prompt, model)
            if result:
                return result
        return None

    def _call_nvidia(self, prompt: str, model: str) -> str:
        url = f"{cfg.NVIDIA_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.nvidia_key}", 
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=600)
            
            if resp.status_code == 410:
                print(f"[NVIDIA] Model {model} EOL (410), trying next...")
                return None
            if resp.status_code != 200:
                print(f"[NVIDIA] {model} Error {resp.status_code}: {resp.text[:200]}")
                return None
            
            data = resp.json()
            
            if "choices" not in data:
                print(f"[NVIDIA] {model} Invalid response format")
                return None
                
            return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"[NVIDIA {model}] Exception: {e}")
            return None

    def _try_gemini_models(self, prompt: str) -> str:
        if not self.gemini_key:
            return None
            
        for model in self.gemini_models:
            if not model:
                continue
            result = self._call_gemini(prompt, model)
            if result:
                return result
        return None

    def _call_gemini(self, prompt: str, model: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": self.gemini_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
        }
        
        try:
            resp = requests.post(url, params=params, json=payload, timeout=600)
            
            if resp.status_code == 404:
                print(f"[Gemini] Model {model} not found (404), trying next...")
                return None
            if resp.status_code != 200:
                print(f"[Gemini] {model} Error {resp.status_code}: {resp.text[:200]}")
                return None
            
            data = resp.json()
            
            if "candidates" not in data:
                if "error" in data:
                    print(f"[Gemini] {model} API Error: {data['error'].get('message', 'Unknown')}")
                else:
                    print(f"[Gemini] {model} Invalid response format")
                return None
                
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
        except Exception as e:
            print(f"[Gemini {model}] Exception: {e}")
            return None

    def _try_lmstudio(self, prompt: str) -> str:
        """Fallback ke LM Studio lokal"""
        if not self.lmstudio_url:
            return None
        
        # Step 1: Auto-detect loaded model kalau tidak di-set di .env
        model_id = self._get_lmstudio_model()
        if not model_id:
            print("[LMStudio] Tidak ada model yang loaded. Load model di LM Studio terlebih dahulu.")
            return None
        
        print(f"[LMStudio] Using model: {model_id}")
        
        url = f"{self.lmstudio_url}/chat/completions"
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1024,
            "stream": False
        }
        
        try:
            # LM Studio tidak selalu butuh API key
            resp = requests.post(
                url, 
                json=payload, 
                timeout=120  # Local model bisa lambat di first load
            )
            
            if resp.status_code != 200:
                print(f"[LMStudio] Error {resp.status_code}: {resp.text[:300]}")
                return None
            
            data = resp.json()
            
            if "choices" not in data:
                print(f"[LMStudio] Invalid response: {json.dumps(data, indent=2)[:300]}")
                return None
            
            return data["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.ConnectionError:
            print("[LMStudio] Connection refused. Pastikan LM Studio sudah running di", self.lmstudio_url)
            return None
        except Exception as e:
            print(f"[LMStudio] Exception: {e}")
            return None

    def _get_lmstudio_model(self) -> str:
        """Cek model yang sedang loaded di LM Studio"""
        # Kalau sudah di-set di .env, pakai itu
        if cfg.LMSTUDIO_MODEL:
            return cfg.LMSTUDIO_MODEL
            
        # Kalau tidak, auto-detect dari /api/v1/models
        try:
            resp = requests.get(
                f"{self.lmstudio_url}/models", 
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("data", [])
                if models:
                    # Ambil model pertama yang loaded
                    return models[0].get("id", "")
        except Exception as e:
            print(f"[LMStudio] Auto-detect failed: {e}")
        
        # Fallback ke daftar model yang mungkin kamu punya
        for model in self.lmstudio_models:
            if model:
                return model
        return ""

summarizer = AISummarizer()
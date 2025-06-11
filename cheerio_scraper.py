# cheerio_scraper.py
import requests
import traceback

PUPPETEER_RENDER_URL = "https://controll-puppeteer.onrender.com/scrape"

def run_cheerio_scrape(target_url):
    try:
        response = requests.post(PUPPETEER_RENDER_URL, json={"url": target_url}, timeout=20)
        if response.status_code == 200:
            return response.text
        else:
            print(f"🛑 Puppeteer scrape failed: {response.status_code}")
            return ""
    except Exception as e:
        print(f"❌ Exception in run_cheerio_scrape: {e}")
        print(traceback.format_exc())
        return ""

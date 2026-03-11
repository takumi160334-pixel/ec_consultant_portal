import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
import json
import os
import feedparser
import requests
import time

# Data output paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'data')
RAW_YOUTUBE_FILE = os.path.join(DATA_DIR, 'raw_youtube.json')
RAW_RSS_FILE = os.path.join(DATA_DIR, 'raw_rss.json')

TARGET_CHANNELS = [
    "https://www.youtube.com/@proteinum_ec/videos",
    "https://www.youtube.com/@ecgrowth/videos",
    "https://www.youtube.com/@EC-hack/videos",
    "https://www.youtube.com/@LANY_SEO/videos",  # SEO/Content Marketing
    "https://www.youtube.com/@seovideo1/videos"    # Google SEO Updates
]

RSS_FEEDS = [
    {'url': 'https://netshop.impress.co.jp/rss.xml', 'name': 'ネットショップ担当者フォーラム'},
    {'url': 'https://ecnomikata.com/rss/', 'name': 'ECのミカタ'},
    {'url': 'https://note.com/hashtag/E%E3%82%B3%E3%83%9E%E3%83%BC%E3%82%B9/rss', 'name': 'note (Eコマース)'},
    {'url': 'https://note.com/hashtag/ChatGPT/rss', 'name': 'note (ChatGPT/LLM)'},
    {'url': 'https://note.com/hashtag/SNS%E3%83%9E%E3%83%BC%E3%82%B1%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0/rss', 'name': 'note (SNSマーケティング)'},
    {'url': 'https://markezine.jp/rss/new/', 'name': 'MarkeZine (デジタルマーケティング)'},
    {'url': 'https://note.com/pala_kojima/m/m5ef2dede0629/rss', 'name': 'note (EC事業の現場)'},
    {'url': 'https://www.ecmj.co.jp/column/feed/', 'name': 'ECマーケティング人財育成 (ECMJ)'},
    {'url': 'https://www.commerce-design.net/blog/feed/', 'name': 'コマースデザイン EC研究所'},
    {'url': 'https://www.commerce-design.net/blog-staff/feed/', 'name': 'コマースデザイン スタッフブログ'}
]

def fetch_youtube_video_ids(channel_url):
    """Fetches video IDs from a YouTube channel URL."""
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'playlistend': 3 # LIMIT FOR TESTING
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                return [{'id': entry['id'], 'title': entry['title']} for entry in info['entries']]
        except Exception as e:
            print(f"Error fetching channel {channel_url}: {e}")
    return []

def fetch_transcript(video_id):
    """Fetches Japanese transcript."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        full_text = " ".join([t['text'] for t in transcript])
        return full_text
    except Exception as e:
        print(f"No JP transcript found for {video_id}: {e}")
        return None

def process_youtube_knowledge():
    print("--- Starting YouTube Knowledge Extraction ---")
    raw_knowledge = []
    
    for channel in TARGET_CHANNELS:
        print(f"Fetching from: {channel}")
        videos = fetch_youtube_video_ids(channel)
        
        for video in videos:
            print(f"  - Scraping transcript for: {video['title']} ({video['id']})")
            transcript = fetch_transcript(video['id'])
            if transcript:
                raw_knowledge.append({
                    "title": video['title'],
                    "source_url": f"https://www.youtube.com/watch?v={video['id']}",
                    "text": transcript,
                    "type": "youtube"
                })
    
    with open(RAW_YOUTUBE_FILE, 'w', encoding='utf-8') as f:
        json.dump(raw_knowledge, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(raw_knowledge)} raw YouTube transcripts.")

def process_rss_knowledge():
    print("--- Starting RSS Extraction ---")
    raw_rss_data = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for feed in RSS_FEEDS:
        print(f"Fetching RSS: {feed['name']}")
        try:
            r = requests.get(feed['url'], headers=headers, timeout=10)
            r.raise_for_status()
            
            d = feedparser.parse(r.content)
            # Take top 5 entries per feed
            for entry in d.entries[:5]: 
                raw_rss_data.append({
                    "title": entry.title,
                    "source_url": entry.link,
                    "text": entry.summary if hasattr(entry, 'summary') else entry.title, # Summary text or fallback to title
                    "type": "rss",
                    "source_name": feed['name']
                })
        except Exception as e:
            print(f"Error fetching {feed['name']}: {e}")

    with open(RAW_RSS_FILE, 'w', encoding='utf-8') as f:
        json.dump(raw_rss_data, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(raw_rss_data)} raw RSS entries.")

if __name__ == "__main__":
    process_youtube_knowledge()
    process_rss_knowledge()

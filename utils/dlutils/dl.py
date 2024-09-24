import os
from colorama import Fore, Style
from config import *
import yt_dlp as youtube_dl

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.18363',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36'
]

def download_video(video_url, download_path):
    quality_map = {
        'low': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        'medium': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'high': 'bestvideo+bestaudio/best'
    }

    def attempt_download(user_agent=None):
        ydl_opts = {
            'format': quality_map[DOWNLOAD_QUALITY],
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ffmpeg_location': FFMPEG_PATH,
            'geo-bypass': GEO_BYPASS,
            'no-part': True,
            'console-title': True,
            'concurrent-fragments': CONCURRENT_FRAGMENTS,
            'http_headers': {'User-Agent': user_agent} if user_agent else {}
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return True
        except Exception as e:
            print(f"{Fore.RED}Failed to download {video_url} with user agent {user_agent}: {e}{Style.RESET_ALL}")
            return False

    if attempt_download():
        return

    for user_agent in USER_AGENTS:
        if attempt_download(user_agent):
            return

    print(f"{Fore.RED}All attempts to download {video_url} failed.{Style.RESET_ALL}")
import os
from colorama import Fore, Style
from config import *
import yt_dlp as youtube_dl

def download_video(video_url, download_path):
    quality_map = {
        'low': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        'medium': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'high': 'bestvideo+bestaudio/best'
    }
    ydl_opts = {
        'format': quality_map[DOWNLOAD_QUALITY],
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'ffmpeg_location': FFMPEG_PATH,
        'geo-bypass': GEO_BYPASS,
        'no-part': True,
        'console-title': True,
        'concurrent-fragments': CONCURRENT_FRAGMENTS
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"{Fore.RED}Failed to download {video_url}: {e}{Style.RESET_ALL}")
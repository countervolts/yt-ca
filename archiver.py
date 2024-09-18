import os
import re
import time
from tqdm import tqdm
from datetime import timedelta, datetime
from colorama import init, Fore, Style
import yt_dlp as youtube_dl
from googleapiclient.discovery import build

config_file = 'config.py'

if not os.path.exists(config_file):
    api_key = input("enter your youtube data v3 api key: ")
    skip_shorts = input("do you want to skip shorts? (yes/no): ").strip().lower() == 'yes'
    print("video download quality: l (low, 480p), m (medium, 720p), H (high, highest available)")
    download_quality = input("enter download quality: ").strip().lower()
    geo_bypass = input("would you like to bypass geo restrictions? (y/n): ").lower()
    ffmpeg_path = input("enter the path to ffmpeg: ")

    os.system('cls' if os.name == 'nt' else 'clear')
    
    quality_map = {'l': 'low', 'm': 'medium', 'h': 'high'}
    download_quality = quality_map.get(download_quality, 'medium')

    with open(config_file, 'w') as f:
        f.write(f"API_KEY = '{api_key}'\n")
        f.write(f"SKIP_SHORTS = {skip_shorts}\n")
        f.write(f"DOWNLOAD_QUALITY = '{download_quality}'\n")
        f.write(f"GEO_BYPASS = 's{geo_bypass}'\n")
        f.write(f"FFMPEG_PATH = '{ffmpeg_path}'\n")
        f.write(f"YOUTUBE_API_SERVICE_NAME = 'youtube'\n")
        f.write(f"YOUTUBE_API_VERSION = 'v3'\n")

    from config import *
else:
    from config import *

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

init()

def get_channel_id(channel_name):
    request = youtube.search().list(
        q=channel_name,
        part='snippet',
        type='channel',
        maxResults=1
    )
    response = request.execute()
    return response['items'][0]['snippet']['channelId']

def get_video_ids(channel_id):
    video_ids = []
    request = youtube.search().list(
        channelId=channel_id,
        part='id,snippet',
        order='date',
        maxResults=50
    )
    while request:
        response = request.execute()
        for item in response['items']:
            if 'videoId' in item['id']:
                video_ids.append({'id': item['id']['videoId'], 'title': item['snippet']['title']})
        request = youtube.search().list_next(request, response)
    return video_ids

def get_video_details(video_ids):
    video_details = []
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part='contentDetails,snippet',
            id=','.join([video['id'] for video in video_ids[i:i+50]])
        )
        response = request.execute()
        video_details += response['items']
    return video_details

def parse_duration(duration):
    match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration)
    hours = int(match.group(1)[:-1]) if match.group(1) else 0
    minutes = int(match.group(2)[:-1]) if match.group(2) else 0
    seconds = int(match.group(3)[:-1]) if match.group(3) else 0
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

def is_short(video):
    duration = parse_duration(video['contentDetails']['duration'])
    return duration < timedelta(minutes=1)

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
        'no-part': True
        }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"{Fore.RED}Failed to download {video_url}: {e}{Style.RESET_ALL}")

def print_status(video_details, downloaded_count, download_path, current_video, elapsed_times, total_size_estimate):
    total_videos = len(video_details)
    remaining_videos = total_videos - downloaded_count
    total_duration = sum([parse_duration(video['contentDetails']['duration']).total_seconds() for video in video_details[:downloaded_count]])
    total_duration_str = str(timedelta(seconds=total_duration))
    total_size = sum(os.path.getsize(os.path.join(download_path, f)) for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f)))
    total_size_str = f"{total_size / (1024 * 1024):.2f} MB"
    
    current_video_duration = parse_duration(current_video['contentDetails']['duration'])
    current_video_duration_str = str(current_video_duration)
    current_video_release_date = datetime.strptime(current_video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d %Y')

    if elapsed_times:
        avg_time_per_video = sum(elapsed_times) / len(elapsed_times)
        est_time_remaining = avg_time_per_video * remaining_videos
    else:
        est_time_remaining = 0

    est_time_remaining_str = str(timedelta(seconds=est_time_remaining))

    print(f"{Fore.CYAN}videos remaining: {Fore.YELLOW}{downloaded_count}/{remaining_videos}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}time downloaded: {Fore.YELLOW}{total_duration_str}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}est total size on disk: {Fore.YELLOW}{total_size_estimate}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}total size on disk: {Fore.YELLOW}{total_size_str}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}est time remaining: {Fore.YELLOW}{est_time_remaining_str}{Style.RESET_ALL}")
    print()
    print(f"{Fore.CYAN}currently downloading: {Fore.YELLOW}{current_video['snippet']['title']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}video length: {Fore.YELLOW}{current_video_duration_str}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}release date: {Fore.YELLOW}{current_video_release_date}{Style.RESET_ALL}")

def main():
    channel_name = input("Enter YouTube channel name: ")
    channel_id = get_channel_id(channel_name)
    video_ids = get_video_ids(channel_id)
    video_details = get_video_details(video_ids)

    global total_size_estimate
    skip_calculation = input("Do you want to skip the size calculation? (yes/no): ").strip().lower()
    if skip_calculation == 'yes':
        total_size_estimate = "Skipped"
    else:
        print("Calculating total size estimate...")
        size_estimate_map = {
            'low': 500,  
            'medium': 1000, 
            'high': 1500  
        }
        est_size_per_hour = size_estimate_map[DOWNLOAD_QUALITY]
        total_size_estimate = 0
        for video in tqdm(video_details, desc="Calculating size", unit="video"):
            duration = parse_duration(video['contentDetails']['duration'])
            total_size_estimate += (duration.total_seconds() / 3600) * est_size_per_hour
        total_size_estimate = f"{total_size_estimate / 1024:.2f} GB"

    total_duration = timedelta()
    for video in video_details:
        duration = parse_duration(video['contentDetails']['duration'])
        total_duration += duration

    oldest_video = None
    newest_video = None

    for video in video_details:
        if not (SKIP_SHORTS and is_short(video)):
            if oldest_video is None:
                oldest_video = video['snippet']['title']
            newest_video = video['snippet']['title']

    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}Channel: {Fore.YELLOW}{channel_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Videos: {Fore.YELLOW}{len(video_details)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total Length: {Fore.YELLOW}{total_duration}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}est size: {Fore.YELLOW}{total_size_estimate}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}size Calculation: {Fore.YELLOW}{DOWNLOAD_QUALITY} quality{Style.RESET_ALL}")
    if oldest_video:
        print(f"{Fore.CYAN}Newest Video: {Fore.YELLOW}{oldest_video}{Style.RESET_ALL}")
    if newest_video:
        print(f"{Fore.CYAN}Oldest Video: {Fore.YELLOW}{newest_video}{Style.RESET_ALL}")

    download_path = input("Enter download location: ")
    os.makedirs(download_path, exist_ok=True)

    print("Starting download...")

    start_time = time.time()
    elapsed_times = []

    for i, video in enumerate(video_details):
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        if SKIP_SHORTS and ('shorts' in video_url or is_short(video)):
            continue
        start_video_time = time.time()
        download_video(video_url, download_path)
        end_video_time = time.time()
        elapsed_times.append(end_video_time - start_video_time)
        print_status(video_details, i + 1, download_path, video, elapsed_times, total_size_estimate)

    end_time = time.time()
    elapsed_time = timedelta(seconds=end_time - start_time)

    total_size = sum(os.path.getsize(os.path.join(download_path, f)) for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f)))
    total_size_str = f"{total_size / (1024 * 1024):.2f} MB"

    with open(os.path.join(download_path, 'post download info.txt'), 'w') as info_file:
        info_file.write(f"channel: {channel_name}\n")
        info_file.write(f"videos downloaded: {len(video_details)}\n")
        info_file.write(f"time it took: {elapsed_time}\n")
        info_file.write(f"est size: {total_size_estimate}\n")
        info_file.write(f"real size: {total_size_str}\n")

    print("Download completed.")

if __name__ == "__main__":
    main()
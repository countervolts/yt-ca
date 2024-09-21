import os
from datetime import timedelta, datetime
import time

if not os.path.exists('config.py'):
    print("run setup.py")
    time.sleep(3)
    exit()

import re
from tqdm import tqdm
from colorama import init, Fore, Style
import yt_dlp as youtube_dl
from googleapiclient.discovery import build
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import psutil
import platform

from compression.compressor import main as compressor_main
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
    if 'contentDetails' not in video or 'duration' not in video['contentDetails']:
        print(f"Skipping video {video.get('snippet', {}).get('title', 'Unknown')} due to missing duration info.")
        return False
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
        'no-part': True,
        'console-title': True,
        'concurrent-fragments': CONCURRENT_FRAGMENTS
        }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"{Fore.RED}Failed to download {video_url}: {e}{Style.RESET_ALL}")

def save_download_path(download_path):
    config_lines = []
    if os.path.exists('config.py'):
        with open('config.py', 'r') as config_file:
            config_lines = config_file.readlines()
    
    with open('config.py', 'w') as config_file:
        path_written = False
        for line in config_lines:
            if line.startswith("DOWNLOAD_PATH"):
                config_file.write(f"DOWNLOAD_PATH = '{download_path}'\n")
                path_written = True
            else:
                config_file.write(line)
        
        if not path_written:
            config_file.write(f"DOWNLOAD_PATH = '{download_path}'\n")

def print_status(video_details, downloaded_count, download_path, current_video, elapsed_times, total_size_estimate):
    total_videos = len(video_details)
    remaining_videos = total_videos - downloaded_count
    
    total_duration = 0
    for video in video_details[:downloaded_count]:
        if 'contentDetails' in video: 
            total_duration += parse_duration(video['contentDetails']['duration']).total_seconds()
    
    total_duration_str = str(timedelta(seconds=total_duration))
    total_size = sum(os.path.getsize(os.path.join(download_path, f)) for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f)))
    total_size_str = f"{total_size / (1024 * 1024):.2f} MB"
    
    current_video_duration = timedelta(0)
    current_video_release_date = "N/A"
    if 'contentDetails' in current_video:
        current_video_duration = parse_duration(current_video['contentDetails']['duration'])
    if 'snippet' in current_video:
        current_video_release_date = datetime.strptime(current_video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d %Y')

    current_video_duration_str = str(current_video_duration)

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
    print(f"\n{Fore.CYAN}currently downloading: {Fore.YELLOW}{current_video['snippet']['title'] if 'snippet' in current_video else 'N/A'}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}video length: {Fore.YELLOW}{current_video_duration_str}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}release date: {Fore.YELLOW}{current_video_release_date}{Style.RESET_ALL}")

def convert_video(input_file, output_file):
    subprocess.run([FFMPEG_PATH, '-i', input_file, output_file, '-loglevel', 'quiet'])

def convert_videos(download_path, target_format):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_videos = len(video_files)
    start_time = time.time()
    elapsed_times = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for filename in video_files:
            base = os.path.splitext(filename)[0]
            target_file = f"{base}.{target_format}"
            input_file = os.path.join(download_path, filename)
            output_file = os.path.join(download_path, target_file)
            futures.append(executor.submit(convert_video, input_file, output_file))

        for i, future in enumerate(tqdm(as_completed(futures), total=total_videos, desc="Converting videos", unit="video")):
            start_video_time = time.time()
            future.result()
            end_video_time = time.time()
            
            elapsed_times.append(end_video_time - start_video_time)
            avg_time_per_video = sum(elapsed_times) / len(elapsed_times)
            est_time_remaining = avg_time_per_video * (total_videos - (i + 1))
            est_time_remaining_str = str(timedelta(seconds=est_time_remaining))

    total_time = time.time() - start_time
    print(f"All videos converted in {str(timedelta(seconds=total_time))}")

    for filename in video_files:
        os.remove(os.path.join(download_path, filename))
        os.system('cls' if os.name == 'nt' else 'clear')
    print("Original videos deleted.\n")

def info_getter():
    partitions = psutil.disk_partitions()
    main_disk = None

    for partition in partitions:
        if partition.mountpoint == '/' or partition.mountpoint == 'C:\\':
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                main_disk = (partition.device, usage)
                break
            except PermissionError:
                continue

    os_info = platform.system()
    if os_info == 'Darwin':
        os_info = 'Darwin (MacOS)'

    if main_disk:
        device, usage = main_disk
        total_storage = usage.total
        total_used = usage.used

        print("\nMain Disk Information:")
        print(f"{device} - {usage.used / (1024 ** 3):.2f}/{usage.total / (1024 ** 3):.2f} GB used")

        total_storage_tb = total_storage / (1024 ** 4)
        total_used_tb = total_used / (1024 ** 4)
        total_storage_gb = total_storage / (1024 ** 3)
        total_used_gb = total_used / (1024 ** 3)

        print(f"\nTotal Storage: {total_storage_tb:.2f} TB ({total_storage_gb:.2f} GB)")
        print(f"Total Used: {total_used_tb:.2f} TB ({total_used_gb:.2f} GB)\n")
    else:
        print("Main disk not found.")

    print(f"Operating System: {os_info}")

def main():
    total_size_str = "Unknown size"
    total_size_estimate_str = "Unknown size"
    os.system('cls' if os.name == 'nt' else 'clear')
    info_getter()
    channel_name = input("\nEnter YouTube channel name: ")
    channel_id = get_channel_id(channel_name)
    
    base_path = os.path.join('yt_data', channel_id)
    os.makedirs(base_path, exist_ok=True)
    
    channel_info_path = os.path.join(base_path, f'{channel_id}_channel_info.txt')
    video_details_path = os.path.join(base_path, f'{channel_id}_video_details.txt')
    video_ids_path = os.path.join(base_path, f'{channel_id}_video_ids.txt')
    video_details_path = os.path.join(base_path, f'{channel_id}_video_details.txt')
    
    data_loaded_from_saved_files = False
    
    if all(os.path.exists(path) for path in [channel_info_path, video_ids_path, video_details_path]):
        print(f"Data for channel {channel_name} already exists. Loading from saved data...")
        print("You have saved API calls since the data was already saved.")
        
        with open(channel_info_path, 'r') as channel_info_file:
            channel_info = channel_info_file.read()
            print(channel_info)
        
        video_ids = []
        with open(video_ids_path, 'r') as video_ids_file:
            for line in video_ids_file:
                video_id, title = line.strip().split(' - ')
                video_ids.append({'id': video_id, 'title': title})
        
        video_details = []
        with open(video_details_path, 'r') as video_details_file:
            video_detail = {}
            for line in video_details_file:
                if line.strip() == "":
                    video_details.append(video_detail)
                    video_detail = {}
                else:
                    key, value = line.strip().split(': ', 1)
                    video_detail[key.lower().replace(' ', '_')] = value
        
        total_size_estimate_str = "Previously calculated size"
        data_loaded_from_saved_files = True
    else:
        print(f"Fetching data for channel {channel_name} from YouTube API...")
        
        with open(channel_info_path, 'w') as channel_info_file:
            channel_info_file.write(f"Channel Name: {channel_name}\n")
            channel_info_file.write(f"Channel ID: {channel_id}\n")
        
        video_ids = get_video_ids(channel_id)
        
        with open(video_ids_path, 'w') as video_ids_file:
            for video in video_ids:
                video_ids_file.write(f"{video['id']} - {video['title']}\n")
        
        video_details = get_video_details(video_ids)
        
        with open(video_details_path, 'w') as video_details_file:
            for video in video_details:
                video_details_file.write(f"ID: {video['id']}\n")
                video_details_file.write(f"Title: {video['snippet']['title']}\n")
                video_details_file.write(f"Duration: {video['contentDetails']['duration']}\n")
                video_details_file.write(f"Published At: {video['snippet']['publishedAt']}\n")
                video_details_file.write("\n")
    
    if not data_loaded_from_saved_files:
        total_size_estimate = 0
        print("Calculating total size estimate...")
        size_estimate_map = {
            'low': 500 * 1024 * 1024,
            'medium': 1000 * 1024 * 1024,
            'high': 1500 * 1024 * 1024
        }
        est_size_per_hour = size_estimate_map[DOWNLOAD_QUALITY]
        
        for video in tqdm(video_details, desc="Calculating size", unit="video"):
            duration = parse_duration(video['contentDetails']['duration'])
            total_size_estimate += (duration.total_seconds() / 3600) * est_size_per_hour
        total_size_estimate_str = f"{total_size_estimate / (1024 ** 3):.2f} GB"

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
        print(f"{Fore.CYAN}channel: {Fore.YELLOW}{channel_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}videos: {Fore.YELLOW}{len(video_details)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}total length: {Fore.YELLOW}{total_duration}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}est size: {Fore.YELLOW}{total_size_estimate_str}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}size calculation: {Fore.YELLOW}{DOWNLOAD_QUALITY} quality{Style.RESET_ALL}")
        if oldest_video:
            print(f"{Fore.CYAN}Oldest Video: {Fore.YELLOW}{oldest_video}{Style.RESET_ALL}")
        if newest_video:
            print(f"{Fore.CYAN}Newest Video: {Fore.YELLOW}{newest_video}{Style.RESET_ALL}")

    download_path = input("Enter the download location: ").strip()
    os.makedirs(download_path, exist_ok=True)

    save_download_path(download_path)

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
        print_status(video_details, i + 1, download_path, video, elapsed_times, total_size_str) 
    end_time = time.time()
    elapsed_time = timedelta(seconds=end_time - start_time)

    total_size = sum(os.path.getsize(os.path.join(download_path, f)) for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f)))
    total_size_str = f"{total_size / (1024 * 1024):.2f} MB"

    with open(os.path.join(base_path, f'{channel_id}_post_download_info.txt'), 'w') as info_file:
        info_file.write(f"channel: {channel_name}\n")
        info_file.write(f"videos downloaded: {len(video_details)}\n")
        info_file.write(f"time it took: {elapsed_time}\n")
        info_file.write(f"est size: {total_size_estimate_str}\n") 
        info_file.write(f"real size: {total_size_str}\n")
        info_file.write("\ndownloaded URLs:\n")
        for video in video_details:
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            info_file.write(f"{video_url}\n")

    print("Downloading done\n")
    os.system('cls' if os.name == 'nt' else 'clear')

    convert_choice = input("Do you want to convert the downloaded videos to a different format? (yes/no): ").strip().lower()
    if convert_choice == 'yes':
        target_format = input("Enter the target format (e.g., mp4, mov): ").strip().lower()
        os.system('cls' if os.name == 'nt' else 'clear')
        convert_videos(download_path, target_format)
        compress_choice = input("Do you want to compress the converted videos? (yes/no): ").strip().lower()
        if compress_choice == 'yes':
            compressor_main()  
    else:
        compress_choice = input("Do you want to compress the downloaded videos? (yes/no): ").strip().lower()
        if compress_choice == 'yes':
            compressor_main()
            os.system('cls' if os.name == 'nt' else 'clear')   

if __name__ == "__main__":
    main()
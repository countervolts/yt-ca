import os
import time as time_module
from datetime import datetime, timedelta

from tqdm import tqdm
from colorama import init, Fore, Style
from googleapiclient.discovery import build

from compression.compressor import main as compressor_main
from convert.local import convert_videos as convert_main
from config import API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, DOWNLOAD_QUALITY, SKIP_SHORTS
from utils.misc.misc import *
from utils.ytutils.ythelper import *
from utils.dlutils.dl import *
from utils.dlutils.path import *

check_config()

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

init()

def main():
    total_size_str = "Unknown size"
    total_size_estimate_str = "Unknown size"
    os.system('cls' if os.name == 'nt' else 'clear')
    info_getter()
    channel_name = input("\nEnter YouTube channel name: ")
    channel_id, display_name = get_channel_id(channel_name)

    base_path = os.path.join('yt_data', channel_id)
    os.makedirs(base_path, exist_ok=True)

    channel_info_path = os.path.join(base_path, f'{channel_id}_channel_info.txt')
    video_details_path = os.path.join(base_path, f'{channel_id}_video_details.txt')
    video_ids_path = os.path.join(base_path, f'{channel_id}_video_ids.txt')

    data_loaded_from_saved_files = False

    if all(os.path.exists(path) for path in [channel_info_path, video_ids_path, video_details_path]):
        print(f"\nData for channel {channel_name} already exists. Loading from saved data...")
        print("You have saved API calls since the data was already saved.\nImported data:\n")

        with open(channel_info_path, 'r', encoding='utf-8') as channel_info_file:
            channel_info = channel_info_file.read()
            print(channel_info)

        video_ids = []
        with open(video_ids_path, 'r', encoding='utf-8') as video_ids_file:
            for line in video_ids_file:
                video_id, title = line.strip().split(' - ')
                video_ids.append({'id': video_id, 'title': title})

        video_details = []
        with open(video_details_path, 'r', encoding='utf-8') as video_details_file:
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

        video_ids = get_video_ids(channel_id)
        num_videos = len(video_ids)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(channel_info_path, 'w', encoding='utf-8') as channel_info_file:
            channel_info_file.write(f"Channel Name: {display_name}\n")
            channel_info_file.write(f"Channel ID: {channel_id}\n")
            channel_info_file.write(f"Number of cached videos: {num_videos}\n")
            channel_info_file.write(f"Data saved on: {timestamp}\n")

        with open(video_ids_path, 'w', encoding='utf-8') as video_ids_file:
            for video in video_ids:
                video_ids_file.write(f"{video['id']} - {video['title']}\n")

        video_details = get_video_details(video_ids)

        with open(video_details_path, 'w', encoding='utf-8') as video_details_file:
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
        print(f"{Fore.CYAN}channel: {Fore.YELLOW}{display_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}videos: {Fore.YELLOW}{len(video_details)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}total length: {Fore.YELLOW}{total_duration}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}est size: {Fore.YELLOW}{total_size_estimate_str}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}size calc: {Fore.YELLOW}{DOWNLOAD_QUALITY} quality{Style.RESET_ALL}")
        if oldest_video:
            print(f"{Fore.CYAN}Oldest Video: {Fore.YELLOW}{oldest_video}{Style.RESET_ALL}")
        if newest_video:
            print(f"{Fore.CYAN}Newest Video: {Fore.YELLOW}{newest_video}{Style.RESET_ALL}")

    download_path = input("Enter the download location: ").strip()
    os.makedirs(download_path, exist_ok=True)

    save_download_path(download_path)

    print("Starting download...")

    start_time = time_module.time()
    elapsed_times = []

    for i, video in enumerate(video_details):
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        if SKIP_SHORTS and ('shorts' in video_url or is_short(video)):
            continue
        start_video_time = time_module.time()
        download_video(video_url, download_path)
        end_video_time = time_module.time()
        elapsed_times.append(end_video_time - start_video_time)
        print_status(video_details, i + 1, download_path, video, elapsed_times, total_size_str)
    end_time = time_module.time()
    elapsed_time = timedelta(seconds=end_time - start_time)

    total_size = sum(os.path.getsize(os.path.join(download_path, f)) for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f)))
    total_size_str = f"{total_size / (1024 * 1024):.2f} MB"

    with open(os.path.join(base_path, f'{channel_id}_post_download_info.txt'), 'w', encoding='utf-8') as info_file:
        info_file.write(f"channel: {display_name}\n")
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
        convert_main(download_path, target_format)

    compress_choice = input("Do you want to compress the videos? (yes/no): ").strip().lower()
    if compress_choice == 'yes':
        compressor_main()
    else:
        print(f"byebye :)")

if __name__ == "__main__":
    main()
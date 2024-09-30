import os
import argparse
from datetime import datetime, timedelta
from tqdm import tqdm
from colorama import init, Fore, Style
import time as time_module

from compress import compress_videos_simple
from utils.misc.misc import info_getter, print_status
from utils.dlutils.dl import download_video
from utils.ytutils.ythelper import parse_duration, is_short

init()

def fetch_channel_data(channel_id):
    base_path = os.path.join('yt_data', channel_id)
    os.makedirs(base_path, exist_ok=True)

    channel_info_path = os.path.join(base_path, f'{channel_id}_channel_info.txt')
    video_details_path = os.path.join(base_path, f'{channel_id}_video_details.txt')
    video_ids_path = os.path.join(base_path, f'{channel_id}_video_ids.txt')

    data_loaded_from_saved_files = False

    if all(os.path.exists(path) for path in [channel_info_path, video_ids_path, video_details_path]):
        print(f"\nData for channel {channel_id} already exists. CLI version will work!\n")

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

        data_loaded_from_saved_files = True
    else:
        print(f"Fetching data for channel {channel_id} from local files...")

        video_ids = [{'id': 'example_video_id', 'title': 'Example Video Title'}]
        video_details = [{'id': 'example_video_id', 'snippet': {'title': 'Example Video Title'}, 'contentDetails': {'duration': 'PT10M'}}]

        num_videos = len(video_ids)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(channel_info_path, 'w', encoding='utf-8') as channel_info_file:
            channel_info_file.write(f"Channel ID: {channel_id}\n")
            channel_info_file.write(f"Number of cached videos: {num_videos}\n")
            channel_info_file.write(f"Data saved on: {timestamp}\n")

        with open(video_ids_path, 'w', encoding='utf-8') as video_ids_file:
            for video in video_ids:
                video_ids_file.write(f"{video['id']} - {video['title']}\n")

        with open(video_details_path, 'w', encoding='utf-8') as video_details_file:
            for video in video_details:
                video_details_file.write(f"ID: {video['id']}\n")
                video_details_file.write(f"Title: {video['snippet']['title']}\n")
                video_details_file.write(f"Duration: {video['contentDetails']['duration']}\n")
                video_details_file.write("\n")

    return channel_id, video_details, data_loaded_from_saved_files

def download_videos(video_details, download_path, download_quality, skip_shorts):
    os.makedirs(download_path, exist_ok=True)

    print("Starting download...")

    start_time = time_module.time()
    elapsed_times = []

    for i, video in enumerate(video_details):
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        if skip_shorts and ('shorts' in video_url or is_short(video)):
            continue
        start_video_time = time_module.time()
        download_video(video_url, download_path, download_quality)
        end_video_time = time_module.time()
        elapsed_times.append(end_video_time - start_video_time)
        print_status(video_details, i + 1, download_path, video, elapsed_times, "Unknown size")
    end_time = time_module.time()
    elapsed_time = timedelta(seconds=end_time - start_time)

    total_size = sum(os.path.getsize(os.path.join(download_path, f)) for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f)))
    total_size_str = f"{total_size / (1024 * 1024):.2f} MB"

    return elapsed_time, total_size_str

def main():
    parser = argparse.ArgumentParser(description="YouTube Channel Archiver CLI")
    parser.add_argument("channel_id", help="ID of the YouTube channel to archive")
    parser.add_argument("download_path", help="Path to download the videos")
    parser.add_argument("-dq", "--download-quality", choices=['l', 'm', 'h'], required=True, help="Download quality (l: low, m: medium, h: high)")
    parser.add_argument("-c", "--compress", choices=['l', 'm', 'h'], help="Enable local compression after downloading with specified level (l: low, m: medium, h: high)")
    parser.add_argument("-ds", "--download-shorts", action='store_true', help="Download YouTube Shorts videos")

    args = parser.parse_args()

    os.system('cls' if os.name == 'nt' else 'clear')
    info_getter()

    channel_id, video_details, data_loaded_from_saved_files = fetch_channel_data(args.channel_id)

    if not data_loaded_from_saved_files:
        total_size_estimate = 0
        print("Calculating total size estimate...")
        size_estimate_map = {
            'l': 500 * 1024 * 1024,
            'm': 1000 * 1024 * 1024,
            'h': 1500 * 1024 * 1024
        }
        est_size_per_hour = size_estimate_map[args.download_quality]

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
            if not (args.download_shorts and is_short(video)):
                if oldest_video is None:
                    oldest_video = video['snippet']['title']
                newest_video = video['snippet']['title']

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.CYAN}channel: {Fore.YELLOW}{channel_id}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}videos: {Fore.YELLOW}{len(video_details)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}total length: {Fore.YELLOW}{total_duration}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}est size: {Fore.YELLOW}{total_size_estimate_str}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}size calc: {Fore.YELLOW}{args.download_quality} quality{Style.RESET_ALL}")
        if oldest_video:
            print(f"{Fore.CYAN}Oldest Video: {Fore.YELLOW}{oldest_video}{Style.RESET_ALL}")
        if newest_video:
            print(f"{Fore.CYAN}Newest Video: {Fore.YELLOW}{newest_video}{Style.RESET_ALL}")

    elapsed_time, total_size_str = download_videos(video_details, args.download_path, args.download_quality, not args.download_shorts)

    with open(os.path.join('yt_data', channel_id, f'{channel_id}_post_download_info.txt'), 'w', encoding='utf-8') as info_file:
        info_file.write(f"channel: {channel_id}\n")
        info_file.write(f"videos downloaded: {len(video_details)}\n")
        info_file.write(f"time it took: {elapsed_time}\n")
        info_file.write(f"real size: {total_size_str}\n")
        info_file.write("\ndownloaded URLs:\n")
        for video in video_details:
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            info_file.write(f"{video_url}\n")

    if args.compress:
        compression_level_map = {
            'l': 'low',
            'm': 'medium',
            'h': 'high'
        }
        compression_level = compression_level_map[args.compress]
        compress_videos_simple(args.download_path, compression_level)

if __name__ == "__main__":
    main()
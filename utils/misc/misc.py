import psutil
import platform
import os
import time as time_module
from datetime import datetime, timedelta
from colorama import Fore, Style
from utils.ytutils.ythelper import *                               
from utils.ytutils.get import *
from utils.dlutils.dl import *
from utils.dlutils.path import *
from utils.misc.misc import *
from config import *

def check_config():
    config = 'config.py'
    
    if not os.path.exists(config):
        print("run setup.py")
        time_module.sleep(3)
        exit()

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

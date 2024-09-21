from .local import compress_videos
from .api import compress_videos_api, update_config
import os

def get_config_value(key):
    config_file = 'config.py'
    if not os.path.exists(config_file):
        return None

    with open(config_file, 'r') as f:
        config = f.readlines()

    config_dict = {}
    for line in config:
        k, v = line.strip().split(' = ')
        config_dict[k] = v.strip("'")

    return config_dict.get(key)

def main():
    compression_method = input("Do you want to compress videos locally or using an API? (local/api): ").strip().lower()
    
    if compression_method == 'api':
        print("\nAvailable API options:")
        print("1. FreeConvert Video Compression API")
        api_choice = input("Enter the number of the API you want to use: ").strip()
        if api_choice == '1':
            api_key = get_config_value('FREECONVERT_API_KEY')
            if not api_key:
                api_key = input("Enter your FreeConvert API key: ").strip()
                update_config('FREECONVERT_API_KEY', api_key)
            download_path = input("Enter the download path: ")
            compress_videos_api(download_path, api_key)
    
    elif compression_method == 'local':
        download_path = input("\nEnter the download path: ")
        vcodec = input("Enter the video codec (default: libx265): ") or 'libx265'
        acodec = input("Enter the audio codec (default: aac): ") or 'aac'
        bitrate = input("Enter the bitrate (default: 1M): ") or '1M'
        crf = int(input("Enter the CRF value (default: 28): ") or 28)
        preset = input("Enter the preset (default: medium): ") or 'medium'
        compress_videos(download_path, vcodec, acodec, bitrate, crf, preset)

    else:
        print("Please choose 'local' or 'api'.")

if __name__ == "__main__":
    main()
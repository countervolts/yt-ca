from .local import main as local_main
from .api import compress_videos_api, update_config
from config import DOWNLOAD_PATH

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
            download_path = DOWNLOAD_PATH
            compress_videos_api(download_path, api_key)
    
    elif compression_method == 'local':
        local_main()
    else:
        print("Please choose 'local' or 'api'.")

if __name__ == "__main__":
    main()
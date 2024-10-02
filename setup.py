import os
import subprocess
import sys
import time

required_packages = [
    'tqdm',
    'colorama',
    'yt-dlp',
    'google-api-python-client',
    'psutil',
    'platform',
    'moviepy'
]

def is_package_installed(package_name):
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

total_packages = len(required_packages)
for i, package in enumerate(required_packages, start=1):
    package_name = package.split('==')[0] 
    if not is_package_installed(package_name):
        print(f"Downloading needed packages [{i}/{total_packages}]")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])
    else:
        print(f"Package '{package}' is already installed [{i}/{total_packages}]")

script_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(script_dir, 'config.py')

def update_config():
    with open(config_file, 'r') as f:
        config = f.readlines()

    config_dict = {}
    for line in config:
        key, value = line.strip().split(' = ')
        config_dict[key] = value.strip("'")

    def prompt_update(key, current_value):
        new_value = input(f"Current {key} is '{current_value}'. Enter new value or press Enter to keep current: ")
        return new_value if new_value else current_value

    config_dict['API_KEY'] = prompt_update('API_KEY', config_dict['API_KEY'])
    config_dict['SKIP_SHORTS'] = prompt_update('SKIP_SHORTS', config_dict['SKIP_SHORTS'])
    config_dict['DOWNLOAD_QUALITY'] = prompt_update('DOWNLOAD_QUALITY', config_dict['DOWNLOAD_QUALITY'])
    config_dict['GEO_BYPASS'] = prompt_update('GEO_BYPASS', config_dict['GEO_BYPASS'])
    config_dict['CONCURRENT_FRAGMENTS'] = prompt_update('CONCURRENT_FRAGMENTS', config_dict['CONCURRENT_FRAGMENTS'])
    config_dict['FFMPEG_PATH'] = prompt_update('FFMPEG_PATH', config_dict['FFMPEG_PATH'])

    with open(config_file, 'w') as f:
        for key, value in config_dict.items():
            f.write(f"{key} = '{value}'\n")

if not os.path.exists(config_file):
    os.system('cls' if os.name == 'nt' else 'clear')
    api_key = input("enter your youtube data v3 api key: ")
    skip_shorts = input("do you want to skip shorts? (yes/no): ").strip().lower() == 'yes'
    print("video download quality: l (480p), m (720p), H (high, highest available)")
    download_quality = input("enter download quality: ").strip().lower()
    geo_bypass = input("would you like to bypass geo restrictions? (y/n): ").lower() == 'yes'
    concurrent_fragments = 5 if input("would you like to use concurrent fragmenting? (yes/no): ").strip().lower() == 'yes' else 1
    ffmpeg_path = input("enter the path to ffmpeg: ")

    os.system('cls' if os.name == 'nt' else 'clear')
    
    quality_map = {'l': 'low', 'm': 'medium', 'h': 'high'}
    download_quality = quality_map.get(download_quality, 'medium')

    with open(config_file, 'w') as f:
        f.write(f"API_KEY = '{api_key}'\n")
        f.write(f"SKIP_SHORTS = '{skip_shorts}'\n")
        f.write(f"DOWNLOAD_QUALITY = '{download_quality}'\n")
        f.write(f"GEO_BYPASS = '{geo_bypass}'\n")
        f.write(f"CONCURRENT_FRAGMENTS = {concurrent_fragments}\n")
        f.write(f"FFMPEG_PATH = '{ffmpeg_path}'\n")
        f.write(f"YOUTUBE_API_SERVICE_NAME = 'youtube'\n")
        f.write(f"YOUTUBE_API_VERSION = 'v3'\n")
else:
    print("config.py already exists. Do you want to update the settings? (yes/no)")
    if input().strip().lower() == 'yes':
        update_config()

print("All setup is done. Now running the main Python script.")
time.sleep(2.2)
archiver_script = os.path.join(script_dir, 'archiver.py')
subprocess.run([sys.executable, archiver_script])
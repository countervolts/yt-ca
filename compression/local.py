import os
import subprocess
from tqdm import tqdm
from colorama import Fore, Style, init

from config import *

init()

def get_file_size(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def get_ffmpeg_codecs():
    result = subprocess.run([FFMPEG_PATH, '-codecs'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    codecs = result.stdout.split('\n')
    vcodecs = [line.split()[1] for line in codecs if 'V.....' in line]
    acodecs = [line.split()[1] for line in codecs if '.A....' in line]
    return vcodecs, acodecs

def color_codecs(codecs):
    colors = [Fore.GREEN, Fore.YELLOW, Fore.RED]
    colored_codecs = []
    for i, codec in enumerate(codecs):
        color = colors[min(i // (len(codecs) // len(colors)), len(colors) - 1)]
        colored_codecs.append(f"{color}{codec}{Style.RESET_ALL}")
    return colored_codecs

def estimate_savings(vcodec, acodec, original_size):
    vcodec_efficiency = {'libx265': 0.5, 'libx264': 0.7, 'mpeg4': 0.8}
    acodec_efficiency = {'aac': 0.7, 'mp3': 0.8, 'vorbis': 0.6}
    v_efficiency = vcodec_efficiency.get(vcodec, 1)
    a_efficiency = acodec_efficiency.get(acodec, 1)
    estimated_size = original_size * v_efficiency * a_efficiency
    return original_size - estimated_size

def compress_video(input_file, output_file, vcodec='libx265', acodec='aac', bitrate='1M', crf=28, preset='medium'):
    command = [
        FFMPEG_PATH, '-i', input_file, '-vcodec', vcodec, '-acodec', acodec,
        '-b:v', bitrate, '-crf', str(crf), '-preset', preset, output_file, '-loglevel', 'quiet'
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Compression failed for {input_file}: {e}")

def get_video_codecs():
    return [
        'libx265', 
        'libx264',
        'mpeg4',
        'libvpx',
        'libxvid'
    ]

def get_audio_codecs():
    return [
        'aac',     
        'mp3',
        'vorbis',
        'opus',
        'pcm_s16le'
    ]

def display_codecs_with_color(codecs, title):
    print(f"{Fore.CYAN}{title} (sorted for optimization):{Style.RESET_ALL}")
    for codec in codecs:
        print(f"{Fore.GREEN}{codec}{Style.RESET_ALL}", end=', ')
    print()

def display_preset_scale_tips():
    print(f"{Fore.YELLOW}Preset Selection Scale (1-10):{Style.RESET_ALL}")
    print("1 - ultrafast: Fastest encoding, but larger file sizes and lower quality.")
    print("3 - veryfast: Good balance of speed and compression, but not optimal quality.")
    print("6 - medium: Default setting, reasonable quality and compression.")
    print("9 - slow: Better compression and quality, but takes significantly longer.")
    print("choose any number from 1-10: ")

def get_preset_from_selection(selection):
    preset_map = {
        1: 'ultrafast',
        3: 'veryfast',
        6: 'medium',
        9: 'slow'
    }
    return preset_map.get(selection, 'medium')

def compress_videos(download_path, vcodec='libx265', acodec='aac', bitrate='1M', crf=28, preset='medium'):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_original_size = 0
    total_compressed_size = 0
    compression_details = []

    for filename in tqdm(video_files, desc="Compressing videos", unit="video"):
        input_file = os.path.join(download_path, filename)
        temp_output_file = os.path.join(download_path, f"compressed_{filename}")
        original_size = get_file_size(input_file)
        total_original_size += original_size

        try:
            compress_video(input_file, temp_output_file, vcodec, acodec, bitrate, crf, preset)
            compressed_size = get_file_size(temp_output_file)
            total_compressed_size += compressed_size
            compression_details.append((filename, original_size, compressed_size))
            
            os.remove(input_file)
            os.rename(temp_output_file, input_file)
        except RuntimeError as e:
            print(f"\n{Fore.RED}{e}{Style.RESET_ALL}")
            retry = input("Do you want to retry with different settings? (yes/no): ").strip().lower()
            if retry == 'yes':
                break
            else:
                continue

    total_savings = total_original_size - total_compressed_size
    average_savings = total_savings / len(video_files) if video_files else 0

    print("\nCompression Report:")
    for filename, original_size, compressed_size in compression_details:
        print(f"{filename}\t{original_size:.2f}\t{compressed_size:.2f}")
    print(f"Total Original Size: {total_original_size:.2f} MB")
    print(f"Total Compressed Size: {total_compressed_size:.2f} MB")
    print(f"Total Savings: {total_savings:.2f} MB")
    print(f"Average Savings per Video: {average_savings:.2f} MB")

def compress_videos_simple(download_path, compression_level):
    presets = {
        'low': {'vcodec': 'libx264', 'acodec': 'aac', 'bitrate': '2M', 'crf': 23, 'preset': 'fast'},
        'medium': {'vcodec': 'libx265', 'acodec': 'aac', 'bitrate': '1M', 'crf': 28, 'preset': 'medium'},
        'high': {'vcodec': 'libx265', 'acodec': 'aac', 'bitrate': '500k', 'crf': 30, 'preset': 'slow'}
    }
    preset = presets[compression_level]
    compress_videos(download_path, preset['vcodec'], preset['acodec'], preset['bitrate'], preset['crf'], preset['preset'])

def main():
    download_path = DOWNLOAD_PATH
    os.system('cls' if os.name == 'nt' else 'clear')
    mode = input("Choose compression mode (simple/advanced): ").strip().lower()
    if mode == 'simple':
        print(f"{Fore.GREEN}Simple Mode Selected{Style.RESET_ALL}")
        compression_level = input("Choose compression level (low/medium/high): ").strip().lower()
        compress_videos_simple(download_path, compression_level)
    elif mode == 'advanced':
        print(f"{Fore.YELLOW}Advanced Mode Selected{Style.RESET_ALL}")
        compress_videos(download_path)
    else:
        print(f"{Fore.RED}Invalid mode selected. Exiting.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
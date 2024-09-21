import os
import subprocess
from tqdm import tqdm
from colorama import Fore, Style

from config import FFMPEG_PATH

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

def compress_videos(download_path, vcodec='libx265', acodec='aac', bitrate='1M', crf=28, preset='medium'):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_original_size = 0
    total_compressed_size = 0
    compression_details = []

    for filename in tqdm(video_files, desc="Compressing videos", unit="video"):
        input_file = os.path.join(download_path, filename)
        output_file = os.path.join(download_path, f"compressed_{filename}")
        original_size = get_file_size(input_file)
        total_original_size += original_size

        try:
            compress_video(input_file, output_file, vcodec, acodec, bitrate, crf, preset)
            compressed_size = get_file_size(output_file)
            total_compressed_size += compressed_size
            compression_details.append((filename, original_size, compressed_size))
        except RuntimeError as e:
            print(f"\n{Fore.RED}{e}{Style.RESET_ALL}")
            retry = input("Do you want to retry with different settings? (yes/no): ").strip().lower()
            if retry == 'yes':
                vcodecs, acodecs = get_ffmpeg_codecs()
                vcodecs = sorted(vcodecs, key=lambda x: {'libx265': 1, 'libx264': 2, 'mpeg4': 3}.get(x, 4))
                acodecs = sorted(acodecs, key=lambda x: {'aac': 1, 'mp3': 2, 'vorbis': 3}.get(x, 4))
                print("\nAvailable video codecs:")
                print(", ".join(color_codecs(vcodecs)))
                print("\nAvailable audio codecs:")
                print(", ".join(color_codecs(acodecs)))
                vcodec = input("Enter the video codec (default: libx265): ") or 'libx265'
                acodec = input("Enter the audio codec (default: aac): ") or 'aac'
                estimated_savings = estimate_savings(vcodec, acodec, original_size)
                print(f"Estimated savings: {estimated_savings:.2f} MB")
                bitrate = input("Enter the bitrate (default: 1M): ") or '1M'
                crf = int(input("Enter the CRF value (default: 28): ") or 28)
                preset = input("Enter the preset (default: medium): ") or 'medium'
                compress_videos(download_path, vcodec, acodec, bitrate, crf, preset)
                return
            else:
                print("Skipping this video.")
                continue

    total_savings = total_original_size - total_compressed_size
    average_savings = total_savings / len(video_files) if video_files else 0

    print("\nCompression Report:")
    print("Filename\tOriginal Size (MB)\tCompressed Size (MB)")
    for filename, original_size, compressed_size in compression_details:
        print(f"{filename}\t{original_size:.2f}\t{compressed_size:.2f}")
    print(f"Total Original Size: {total_original_size:.2f} MB")
    print(f"Total Compressed Size: {total_compressed_size:.2f} MB")
    print(f"Total Savings: {total_savings:.2f} MB")
    print(f"Average Savings per Video: {average_savings:.2f} MB")
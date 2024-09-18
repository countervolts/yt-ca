import os
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from tqdm import tqdm
from config import *

def get_file_size(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)  # Size in MB

def compress_video(input_file, output_file, vcodec='libx265', acodec='aac', bitrate='1M', crf=28):
    command = [
        FFMPEG_PATH, '-i', input_file, '-vcodec', vcodec, '-acodec', acodec,
        '-b:v', bitrate, '-crf', str(crf), output_file
    ]
    subprocess.run(command, check=True)

def compress_videos(download_path, vcodec='libx265', acodec='aac', bitrate='1M', crf=28):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_videos = len(video_files)
    start_time = time.time()
    elapsed_times = []
    size_report = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for filename in video_files:
            input_file = os.path.join(download_path, filename)
            output_file = os.path.join(download_path, f"compressed_{filename}")
            futures.append(executor.submit(compress_video, input_file, output_file, vcodec, acodec, bitrate, crf))

        for i, future in enumerate(tqdm(as_completed(futures), total=total_videos, desc="Compressing videos", unit="video")):
            start_video_time = time.time()
            future.result()
            end_video_time = time.time()
            
            elapsed_times.append(end_video_time - start_video_time)
            avg_time_per_video = sum(elapsed_times) / len(elapsed_times)
            est_time_remaining = avg_time_per_video * (total_videos - (i + 1))
            est_time_remaining_str = str(timedelta(seconds=est_time_remaining))

            input_file = os.path.join(download_path, video_files[i])
            output_file = os.path.join(download_path, f"compressed_{video_files[i]}")
            original_size = get_file_size(input_file)
            compressed_size = get_file_size(output_file)
            size_report.append((video_files[i], original_size, compressed_size))

    total_time = time.time() - start_time
    print(f"All videos compressed in {str(timedelta(seconds=total_time))}")

    # Calculate total and average savings
    total_original_size = sum(original_size for _, original_size, _ in size_report)
    total_compressed_size = sum(compressed_size for _, _, compressed_size in size_report)
    total_savings = total_original_size - total_compressed_size
    avg_savings = total_savings / total_videos if total_videos > 0 else 0

    # Write the size report to a file
    report_file = os.path.join(download_path, 'compression_report.txt')
    with open(report_file, 'w') as f:
        f.write("Filename\tOriginal Size (MB)\tCompressed Size (MB)\n")
        for filename, original_size, compressed_size in size_report:
            f.write(f"{filename}\t{original_size:.2f}\t{compressed_size:.2f}\n")
        f.write(f"\nTotal Original Size: {total_original_size:.2f} MB\n")
        f.write(f"Total Compressed Size: {total_compressed_size:.2f} MB\n")
        f.write(f"Total Savings: {total_savings:.2f} MB\n")
        f.write(f"Average Savings per Video: {avg_savings:.2f} MB\n")

    print(f"Compression report written to {report_file}")
    print(f"Total Original Size: {total_original_size:.2f} MB")
    print(f"Total Compressed Size: {total_compressed_size:.2f} MB")
    print(f"Total Savings: {total_savings:.2f} MB")
    print(f"Average Savings per Video: {avg_savings:.2f} MB")

if __name__ == "__main__":
    download_path = input("Enter the download path: ")
    vcodec = input("Enter the video codec (default: libx265): ") or 'libx265'
    acodec = input("Enter the audio codec (default: aac): ") or 'aac'
    bitrate = input("Enter the bitrate (default: 1M): ") or '1M'
    crf = int(input("Enter the CRF value (default: 28): ") or 28)
    compress_videos(download_path, vcodec, acodec, bitrate, crf)

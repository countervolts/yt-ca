import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from tqdm import tqdm
from pymovie import Movie
from config import FFMPEG_PATH

def compress_video(input_file, output_file, vcodec='libx265', acodec='aac', bitrate='1M', crf=28):
    movie = Movie(input_file)
    movie.compress(output_file, vcodec=vcodec, acodec=acodec, bitrate=bitrate, crf=crf, ffmpeg_path=FFMPEG_PATH)

def compress_videos(download_path, vcodec='libx265', acodec='aac', bitrate='1M', crf=28):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_videos = len(video_files)
    start_time = time.time()
    elapsed_times = []

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

    total_time = time.time() - start_time
    print(f"All videos compressed in {str(timedelta(seconds=total_time))}")

if __name__ == "__main__":
    download_path = input("Enter the download path: ")
    vcodec = input("Enter the video codec (default: libx265): ") or 'libx265'
    acodec = input("Enter the audio codec (default: aac): ") or 'aac'
    bitrate = input("Enter the bitrate (default: 1M): ") or '1M'
    crf = int(input("Enter the CRF value (default: 28): ") or 28)
    compress_videos(download_path, vcodec, acodec, bitrate, crf)
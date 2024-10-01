'''
import os
import time as time_module
from tqdm import tqdm
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy.editor import VideoFileClip

def convert_video(input_file, output_file):
    try:
        clip = VideoFileClip(input_file)
        clip.write_videofile(output_file, codec='libx264', audio_codec='aac', verbose=False, logger=None)
    except Exception as e:
        raise RuntimeError(f"Conversion failed for {input_file}: {e}")

def convert_videos(download_path, target_format):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_videos = len(video_files)
    start_time = time_module.time()
    elapsed_times = []

    with ThreadPoolExecutor() as executor:
        futures = []
        for filename in video_files:
            base = os.path.splitext(filename)[0]
            target_file = f"{base}.{target_format}"
            input_file = os.path.join(download_path, filename)
            output_file = os.path.join(download_path, target_file)
            futures.append(executor.submit(convert_video, input_file, output_file))

        for i, future in enumerate(tqdm(as_completed(futures), total=total_videos, desc="Converting videos", unit="video")):
            start_video_time = time_module.time()
            future.result()
            end_video_time = time_module.time()
            
            elapsed_times.append(end_video_time - start_video_time)
            avg_time_per_video = sum(elapsed_times) / len(elapsed_times)
            est_time_remaining = avg_time_per_video * (total_videos - (i + 1))
            est_time_remaining_str = str(timedelta(seconds=est_time_remaining))

    total_time = time_module.time() - start_time
    print(f"All videos converted in {str(timedelta(seconds=total_time))}")

    for filename in video_files:
        os.remove(os.path.join(download_path, filename))
        os.system('cls' if os.name == 'nt' else 'clear')
    print("Original videos deleted.\n")
    '''
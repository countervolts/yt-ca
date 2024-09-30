import os
from colorama import Fore, Style
import yt_dlp as youtube_dl
from moviepy.editor import VideoFileClip, AudioFileClip

def download_video(video_url, download_path, download_quality):
    quality_map = {
        'l': 'bestvideo[height<=360]+bestaudio/best',
        'm': 'bestvideo[height<=720]+bestaudio/best',
        'h': 'bestvideo+bestaudio/best'
    }

    ydl_opts = {
        'format': quality_map[download_quality],
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'geo-bypass': True,
        'no-part': True,
        'console-title': True,
        'merge_output_format': 'mp4'
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_file = ydl.prepare_filename(info_dict)
            audio_file = video_file.replace('.mp4', '.m4a')

            if os.path.exists(audio_file):
                video_clip = VideoFileClip(video_file)
                audio_clip = AudioFileClip(audio_file)
                final_clip = video_clip.set_audio(audio_clip)
                final_clip.write_videofile(video_file, codec='libx264', audio_codec='aac')
                audio_clip.close()
                video_clip.close()
                os.remove(audio_file)

        return True
    except Exception as e:
        print(f"{Fore.RED}Failed to download {video_url}: {e}{Style.RESET_ALL}")
        return False

    print(f"{Fore.RED}All attempts to download {video_url} failed.{Style.RESET_ALL}")
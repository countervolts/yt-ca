import os
from tqdm import tqdm
from colorama import Fore, Style, init
from moviepy.editor import VideoFileClip

init()

def get_file_size(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def get_video_bitrate(file_path):
    clip = VideoFileClip(file_path)
    duration = clip.duration 
    file_size = os.path.getsize(file_path)  
    bitrate = (file_size * 8) / duration 
    return bitrate / (1024 * 1024) 

def compress_video(input_file, output_file, target_bitrate):
    try:
        clip = VideoFileClip(input_file)
        clip.write_videofile(output_file, bitrate=f"{target_bitrate}M", codec='libx264', audio_codec='aac', verbose=False, logger=None)
    except Exception as e:
        raise RuntimeError(f"Compression failed for {input_file}: {e}")

def compress_videos(download_path, compression_level):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_original_size = 0
    total_compressed_size = 0
    compression_details = []

    # setting the bitrate to a % of the original bitrate instead of a set value
    # it ensures that the video(s) are compressed and prevents the video from gaining size 
    compression_ratios = {
        'low': 0.7, 
        'medium': 0.45,
        'high': 0.35   
    }
    compression_ratio = compression_ratios[compression_level]

    for filename in tqdm(video_files, desc="Compressing videos", unit="video"):
        input_file = os.path.join(download_path, filename)
        temp_output_file = os.path.join(download_path, f"compressed_{filename}")
        original_size = get_file_size(input_file)
        total_original_size += original_size

        try:
            original_bitrate = get_video_bitrate(input_file)
            target_bitrate = original_bitrate * compression_ratio
            compress_video(input_file, temp_output_file, target_bitrate)
            compressed_size = get_file_size(temp_output_file)
            
            if compressed_size < original_size:
                total_compressed_size += compressed_size
                compression_details.append((filename, original_size, compressed_size))
                os.remove(input_file)
                final_output_file = os.path.join(download_path, filename)
                os.rename(temp_output_file, final_output_file)
            else:
                os.remove(temp_output_file)
                compression_details.append((filename, original_size, original_size))
                total_compressed_size += original_size
                print(f"\n{Fore.YELLOW}Skipping {filename} as compressed size is larger than original size.{Style.RESET_ALL}")
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
    compress_videos(download_path, compression_level)

def main():
    download_path = input("Enter the download path: ").strip()
    os.system('cls' if os.name == 'nt' else 'clear')
    compression_level = input("Choose compression level (low/medium/high): ").strip().lower()
    compress_videos_simple(download_path, compression_level)

if __name__ == "__main__":
    main()
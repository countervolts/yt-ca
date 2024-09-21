import os
import requests

def update_config(key, value):
    config_file = 'config.py'
    with open(config_file, 'r') as f:
        config = f.readlines()

    config_dict = {}
    for line in config:
        k, v = line.strip().split(' = ')
        config_dict[k] = v.strip("'")

    config_dict[key] = value

    with open(config_file, 'w') as f:
        for k, v in config_dict.items():
            f.write(f"{k} = '{v}'\n")

def upload_file_to_freeconvert(file_path, api_key):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.post('https://api.freeconvert.com/v1/process/import/upload', headers=headers)
    if response.status_code == 201:
        return response.json()['id']
    else:
        input(f"Error uploading file: {response.json()}")
        return None

def create_compress_task(import_task_id, input_format, output_format, api_key, vcodec='libx265', crf=28, speed='veryfast'):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    body = {
        "input": import_task_id,
        "input_format": input_format,
        "output_format": output_format,
        "options": {
            "video_codec_compress": vcodec,
            "compress_video": "by_percent",
            "video_compress_percent": "60",
            "video_compress_speed": speed
        }
    }
    response = requests.post('https://api.freeconvert.com/v1/process/compress', headers=headers, json=body)
    if response.status_code == 201:
        return response.json()['id']
    else:
        print(f"Error creating compress task: {response.json()}")
        return None

def compress_videos_api(download_path, api_key):
    video_files = [f for f in os.listdir(download_path) if f.endswith((".mp4", ".mkv", ".webm"))]
    total_original_size = 0
    total_compressed_size = 0
    compression_details = []

    for filename in video_files:
        file_path = os.path.join(download_path, filename)
        original_size = os.path.getsize(file_path) / (1024 * 1024) 
        total_original_size += original_size

        import_task_id = upload_file_to_freeconvert(file_path, api_key)
        if import_task_id:
            input_format = filename.split('.')[-1]
            output_format = input_format
            compress_task_id = create_compress_task(import_task_id, input_format, output_format, api_key)
            if compress_task_id:
                print(f"Compression task created for {filename} with task ID: {compress_task_id}")
                compressed_size = os.path.getsize(file_path) / (1024 * 1024)  
                total_compressed_size += compressed_size
                compression_details.append((filename, original_size, compressed_size))
            else:
                print(f"Failed to create compression task for {filename}\n")
        else:
            print(f"Failed to upload {filename}")

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
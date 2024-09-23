import re
from datetime import timedelta, datetime

def parse_duration(duration):
    match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration)
    hours = int(match.group(1)[:-1]) if match.group(1) else 0
    minutes = int(match.group(2)[:-1]) if match.group(2) else 0
    seconds = int(match.group(3)[:-1]) if match.group(3) else 0
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

def is_short(video):
    if 'contentDetails' not in video or 'duration' not in video['contentDetails']:
        print(f"Skipping video {video.get('snippet', {}).get('title', 'Unknown')} due to missing duration info.")
        return False
    duration = parse_duration(video['contentDetails']['duration'])
    return duration < timedelta(minutes=1)

def save_channel_info(channel_id, display_name, video_count, save_path):
    with open(save_path, 'w') as file:
        file.write(f"Channel Name: {display_name}\n")
        file.write(f"Channel ID: {channel_id}\n")
        file.write(f"Number of cached videos: {video_count}\n")
        file.write(f"Data saved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

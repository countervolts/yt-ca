from googleapiclient.discovery import build
from config import *

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def get_channel_id(channel_name):
    request = youtube.search().list(
        q=channel_name,
        part='snippet',
        type='channel',
        maxResults=1
    )
    response = request.execute()
    channel_id = response['items'][0]['snippet']['channelId']
    display_name = response['items'][0]['snippet']['title']
    return channel_id, display_name

def get_video_ids(channel_id):
    video_ids = []
    request = youtube.search().list(
        channelId=channel_id,
        part='id,snippet',
        order='date',
        maxResults=50
    )
    while request:
        response = request.execute()
        for item in response['items']:
            if 'videoId' in item['id']:
                video_ids.append({'id': item['id']['videoId'], 'title': item['snippet']['title']})
        request = youtube.search().list_next(request, response)
    return video_ids

def get_video_details(video_ids):
    video_details = []
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part='contentDetails,snippet',
            id=','.join([video['id'] for video in video_ids[i:i+50]])
        )
        response = request.execute()
        video_details += response['items']
    return video_details


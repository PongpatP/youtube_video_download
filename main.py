import os
import pandas as pd
import yt_dlp
from googleapiclient.discovery import build
from datetime import datetime
from dotenv import load_dotenv

def get_thairath_videos(api_key, start_date, end_date, max_min):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    ch_request = youtube.search().list(q='thairathnews', type='channel', part='id').execute()
    channel_id = ch_request['items'][0]['id']['channelId']
    
    # ISO Format (RFC 3339)
    published_after = f"{start_date}T00:00:00Z"
    published_before = f"{end_date}T23:59:59Z"
    
    videos = []
    next_page_token = None
    max_sec = max_min * 60

    while True:
        search_request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            publishedAfter=published_after,
            publishedBefore=published_before,
            maxResults=50,
            pageToken=next_page_token,
            type='video',
            order='date'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_request['items']]
        
        details_request = youtube.videos().list(
            part='contentDetails,snippet',
            id=','.join(video_ids)
        ).execute()

        for item in details_request['items']:
            duration_str = item['contentDetails']['duration']
            duration_sec = pd.to_timedelta(duration_str).total_seconds()
            
            if duration_sec <= max_sec:
                videos.append({
                    'title': item['snippet']['title'],
                    'duration_sec': duration_sec,
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                })

        next_page_token = search_request.get('nextPageToken')
        if not next_page_token:
            break

    return pd.DataFrame(videos)

def download_from_dataframe(df):
    ydl_opts = {
        'format': 'best[ext=mp4]/best', 
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in df['url']:
            try:
                print(f"กำลังโหลด: {url}")
                ydl.download([url])
            except Exception as e:
                print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    # 1. ดึงข้อมูลเป็น Pandas DataFrame
    # ใส่ช่วงวันที่ (YYYY-MM-DD) และความยาวไม่เกิน (นาที)
    df_videos = get_thairath_videos(
        api_key=api_key, 
        start_date='2026-02-19', 
        end_date='2026-02-20', 
        max_min=5
    )
    print(df_videos)
    df_videos.to_excel('data.xlsx', index=False)
    
    # 2. ดาวน์โหลดจาก DataFrame
    if not df_videos.empty:
        download_from_dataframe(df_videos)
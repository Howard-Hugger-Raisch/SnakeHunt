import requests
import random


host = 'https://audius-discovery-1.cultur3stake.com'
app_name = 'YOUR_APP_NAME'

# Fetch trending tracks
def get_random_track():
    response = requests.get(f'{host}/v1/tracks/trending?app_name={app_name}')
    if response.status_code == 200:
        tracks = response.json()['data']
        if tracks:
            # Select a random track
            random_track = random.choice(tracks)
            return random_track
    print("Failed to retrieve tracks.")
    return None

# Download the track as MP3
def download_track(track_id, title):
    stream_url = f"{host}/v1/tracks/{track_id}/stream?app_name={app_name}"

    response = requests.get(stream_url, stream=True)
    if response.status_code == 200:
        filename = "sound/music.mp3"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"Track downloaded successfully as '{filename}'")
    else:
        print("Failed to download track.")

# function test:
# track = get_random_track()
# if track:
#     print(f"Downloading: {track['title']} by {track['user']['name']}")
#     track_id = track['id']
#     download_track(track_id, track['title'])
# else:
#     print("No track available to download.")


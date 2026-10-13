from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# API Instances Piped & Cobalt yang disokong oleh server awam
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.privacydev.net",
    "https://piped-api.garudalinux.org",
    "https://pipedapi.mha.fi"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_songs():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Sila masukkan kata kunci carian'}), 400

    results = []
    
    for instance in PIPED_INSTANCES:
        try:
            url = f"{instance}/search?q={query}&filter=music_songs"
            res = requests.get(url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                items = res.json().get('items', [])
                for item in items[:20]:
                    if item.get('type') == 'stream':
                        video_id = item.get('url', '').replace('/watch?v=', '')
                        results.append({
                            'id': video_id,
                            'title': item.get('title'),
                            'uploader': item.get('uploaderName') or 'Artist',
                            'thumbnail': item.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
                if results:
                    break
        except Exception:
            continue

    if not results:
        return jsonify({'error': 'Gagal mengambil data dari YouTube. Sila cuba lagi.'}), 500

    return jsonify({'results': results})

@app.route('/api/get-audio-url', methods=['POST'])
def get_audio_url():
    data = request.json
    video_url = data.get('url')
    
    video_id = None
    if 'watch?v=' in video_url:
        video_id = video_url.split('watch?v=')[-1].split('&')[0]
    elif 'youtu.be/' in video_url:
        video_id = video_url.split('youtu.be/')[-1].split('?')[0]

    if not video_id:
        return jsonify({'error': 'URL Video Tidak Sah'}), 400

    audio_stream_url = None

    for instance in PIPED_INSTANCES:
        try:
            url = f"{instance}/streams/{video_id}"
            res = requests.get(url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                stream_data = res.json()
                audio_streams = stream_data.get('audioStreams', [])
                if audio_streams:
                    # Ambil stream audio berkualiti tinggi
                    audio_streams.sort(key=lambda x: int(x.get('bitrate', 0)), reverse=True)
                    audio_stream_url = audio_streams[0].get('url')
                    break
        except Exception:
            continue

    if audio_stream_url:
        return jsonify({'audio_url': audio_stream_url})
    else:
        return jsonify({'error': 'Gagal mendapatkan stream audio.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
#!/usr/bin/env python3
"""Local server: serves static files + proxies NetEase Cloud Music API.
   Supports short URLs (163cn.tv) and full playlist extraction (all tracks).
"""
import http.server
import urllib.request
import urllib.parse
import json
import re
import ssl

PORT = 8000
STATIC_DIR = '/workspace'

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://music.163.com',
}

def fetch_url(url, timeout=15):
    """Fetch a URL and return the response text."""
    req = urllib.request.Request(url, headers=COMMON_HEADERS)
    resp = urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx)
    return resp.read().decode('utf-8')

def resolve_short_url(url):
    """Follow redirects to get the final URL (for 163cn.tv short links)."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36'
    })
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
    resp = opener.open(req, timeout=10)
    return resp.geturl()

def extract_playlist_id(url):
    """Extract playlist ID from various URL formats."""
    # Direct ID patterns
    m = re.search(r'[?&]id=(\d+)', url)
    if m:
        return m.group(1)
    m = re.search(r'/playlist/(\d+)', url)
    if m:
        return m.group(1)
    return None

def get_playlist_full(pid):
    """Get all tracks from a playlist.
    Step 1: Fetch playlist detail to get all trackIds.
    Step 2: Batch-fetch song details for all IDs.
    Returns: list of {name, artist} dicts.
    """
    # Step 1: Get track IDs
    api_url = f'https://music.163.com/api/v6/playlist/detail?id={pid}'
    raw = fetch_url(api_url)
    data = json.loads(raw)
    pl = data.get('playlist') or data.get('result')
    if not pl:
        raise ValueError('歌单不存在或无法访问')

    track_ids_raw = pl.get('trackIds', [])
    tracks_full = pl.get('tracks', [])

    # If we have trackIds, use them; otherwise fall back to the limited tracks list
    if track_ids_raw:
        all_ids = [t['id'] for t in track_ids_raw]
    else:
        all_ids = [t['id'] for t in tracks_full]

    if not all_ids:
        raise ValueError('歌单中没有歌曲')

    # Step 2: Batch-fetch song details (100 IDs per batch)
    all_songs = []
    batch_size = 100
    for i in range(0, len(all_ids), batch_size):
        batch = all_ids[i:i + batch_size]
        ids_param = urllib.parse.quote(json.dumps(batch))
        detail_url = f'https://music.163.com/api/song/detail?ids={ids_param}'
        try:
            raw_detail = fetch_url(detail_url)
            detail_data = json.loads(raw_detail)
            songs = detail_data.get('songs', [])
            for s in songs:
                artists = [a['name'] for a in s.get('artists', s.get('ar', []))]
                all_songs.append({
                    'name': s.get('name', '未知歌曲'),
                    'artist': ' / '.join(artists),
                })
        except Exception:
            # Skip failed batches
            pass

    # If song detail API failed, fall back to the 10 tracks from playlist detail
    if not all_songs and tracks_full:
        for t in tracks_full:
            artists = [a['name'] for a in t.get('ar', t.get('artists', []))]
            all_songs.append({
                'name': t.get('name', '未知歌曲'),
                'artist': ' / '.join(artists),
            })

    return all_songs


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, code, msg):
        self._send_json(code, {'error': msg})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # API: resolve short URL
        if parsed.path == '/api/resolve':
            qs = urllib.parse.parse_qs(parsed.query)
            url = qs.get('url', [''])[0]
            if not url:
                self._send_error_json(400, 'Missing url parameter')
                return
            try:
                final_url = resolve_short_url(url)
                pid = extract_playlist_id(final_url)
                self._send_json(200, {'url': final_url, 'playlistId': pid})
            except Exception as e:
                self._send_error_json(500, str(e))
            return

        # API: get full playlist (all tracks)
        if parsed.path == '/api/playlist':
            qs = urllib.parse.parse_qs(parsed.query)
            url_or_id = qs.get('id', qs.get('url', ['']))[0]
            if not url_or_id:
                self._send_error_json(400, 'Missing id or url parameter')
                return

            try:
                # Determine if it's a URL or a raw ID
                if url_or_id.startswith('http'):
                    pid = extract_playlist_id(url_or_id)
                    if not pid:
                        # Try resolving as short URL
                        final_url = resolve_short_url(url_or_id)
                        pid = extract_playlist_id(final_url)
                    if not pid:
                        self._send_error_json(400, '无法识别歌单ID')
                        return
                else:
                    pid = url_or_id

                songs = get_playlist_full(pid)
                self._send_json(200, {
                    'songs': songs,
                    'count': len(songs),
                    'playlistId': pid,
                })
            except ValueError as e:
                self._send_error_json(400, str(e))
            except Exception as e:
                self._send_error_json(500, str(e))
            return

        # Default: serve static files
        super().do_GET()


if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Server running on http://localhost:{PORT}')
    print(f'  Static files: {STATIC_DIR}')
    print(f'  Full playlist: http://localhost:{PORT}/api/playlist?id=xxx')
    print(f'  URL resolver:  http://localhost:{PORT}/api/resolve?url=xxx')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.shutdown()

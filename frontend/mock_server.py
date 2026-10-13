import http.server
import socketserver
import json
import time
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

MOCK_STREAM_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a202c"/>
      <stop offset="60%" stop-color="#2d3748"/>
      <stop offset="100%" stop-color="#1a202c"/>
    </linearGradient>
    <linearGradient id="road" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2d3748"/>
      <stop offset="100%" stop-color="#171923"/>
    </linearGradient>
  </defs>
  <!-- Background Scene -->
  <rect width="640" height="480" fill="url(#bg)"/>
  <!-- Perspective Road -->
  <polygon points="260,260 380,260 580,480 60,480" fill="url(#road)"/>
  <line x1="320" y1="260" x2="320" y2="480" stroke="#718096" stroke-dasharray="16,12" stroke-width="4"/>
  <!-- Simulated Car Silhouette around bbox [120, 80, 280, 250] -->
  <g transform="translate(130, 95)">
    <rect x="5" y="45" width="140" height="70" rx="10" fill="#e53e3e" opacity="0.9"/>
    <path d="M 22 45 L 42 12 L 108 12 L 128 45 Z" fill="#c53030" opacity="0.95"/>
    <!-- Windows -->
    <polygon points="46,16 68,16 68,42 30,42" fill="#63b3ed" opacity="0.8"/>
    <polygon points="74,16 104,16 122,42 74,42" fill="#63b3ed" opacity="0.8"/>
    <!-- Wheels -->
    <circle cx="35" cy="115" r="15" fill="#171923"/>
    <circle cx="35" cy="115" r="6" fill="#a0aec0"/>
    <circle cx="115" cy="115" r="15" fill="#171923"/>
    <circle cx="115" cy="115" r="6" fill="#a0aec0"/>
    <!-- Headlights -->
    <rect x="12" y="70" width="14" height="10" rx="3" fill="#fef08a"/>
    <rect x="124" y="70" width="14" height="10" rx="3" fill="#fef08a"/>
  </g>
  <!-- Camera HUD Crosshairs & Grid -->
  <circle cx="320" cy="240" r="45" fill="none" stroke="#48bb78" stroke-width="1" stroke-dasharray="4,4" opacity="0.7"/>
  <line x1="295" y1="240" x2="345" y2="240" stroke="#48bb78" stroke-width="1.5" opacity="0.8"/>
  <line x1="320" y1="215" x2="320" y2="265" stroke="#48bb78" stroke-width="1.5" opacity="0.8"/>
  <!-- Status Text overlay -->
  <text x="20" y="32" fill="#48bb78" font-family="monospace" font-size="14" font-weight="bold">ESP32-CAM [640x480 @ 30FPS]</text>
  <text x="20" y="52" fill="#a0aec0" font-family="monospace" font-size="11">SIMULATED FEED • SENSOR SYNC OK</text>
</svg>"""

class VisionDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # 1. Mock API endpoint
        if self.path == '/api/latest':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()

            mock_data = {
                "timestamp": str(time.time()),
                "distance_m": 1.5,
                "objects": [
                    {
                        "class": "car",
                        "confidence": 0.92,
                        "bbox": [120, 80, 280, 250],
                        "position": "center",
                        "angle_deg": 3,
                        "estimated_size": "large",
                        "priority": "high"
                    }
                ],
                "message": "Large obstacle ahead, 1.5 meters away."
            }
            self.wfile.write(json.dumps(mock_data).encode('utf-8'))
            return

        # 2. Mock camera stream endpoint
        elif self.path == '/api/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(MOCK_STREAM_SVG.encode('utf-8'))
            return

        # 3. Serve frontend static files (index.html, style.css, app.js)
        return super().do_GET()

def run_server(port=PORT):
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), VisionDashboardHandler) as httpd:
            print(f"Server started at http://localhost:{port}/")
            httpd.serve_forever()
    except OSError:
        # Fallback to port 8080 if 3000 is taken
        fallback_port = 8080
        with socketserver.TCPServer(("", fallback_port), VisionDashboardHandler) as httpd:
            print(f"Server started at http://localhost:{fallback_port}/")
            httpd.serve_forever()

if __name__ == '__main__':
    run_server()

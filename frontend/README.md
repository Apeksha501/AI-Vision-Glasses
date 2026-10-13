# Smart Vision Dashboard (Frontend)

Interactive web dashboard for the **AI and IoT Enabled Smart Vision Assistance System**.

## Features
- **Live Camera Feed**: Displays ESP32 camera stream with dynamic YOLO bounding box overlays.
- **Real-Time Obstacle Telemetry**: Live metrics for detected objects, confidence, horizontal angle, distance, estimated size, and threat priority.
- **Visual Alert Banner**: Real-time assistive notifications color-coded by obstacle risk level.
- **Connection Indicator**: Live status monitor verifying connection to the backend.

## Local Testing
To preview the dashboard locally with simulated ESP32 & YOLO telemetry:
```bash
python3 mock_server.py
```
Then open: `http://localhost:3000/`

## Backend Integration
When connecting to the live ESP32-CAM and YOLO backend:
- The backend should expose:
  - `GET /api/stream`: MJPEG live camera stream
  - `GET /api/latest`: Real-time JSON telemetry (object label, bbox, distance, angle, priority, and voice prompt)
- Set `API_URL` in `app.js` to point to your live backend endpoint.

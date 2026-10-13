const API_URL = '/api/latest';
const POLL_INTERVAL_MS = 1000; // Fetch data every 1 second

// Original camera feed resolution from ESP32 used for bounding box calculations
const CAMERA_WIDTH = 640;
const CAMERA_HEIGHT = 480;

async function fetchLatestData() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        updateUI(data);
        setConnectionStatus(true);
    } catch (error) {
        console.error('Error fetching data:', error);
        setConnectionStatus(false);
    }
}

function setConnectionStatus(isConnected) {
    const dot = document.getElementById('connection-status');
    const text = document.getElementById('status-text');
    if (isConnected) {
        dot.className = 'status-dot connected';
        text.textContent = 'Connected';
    } else {
        dot.className = 'status-dot disconnected';
        text.textContent = 'Disconnected';
    }
}

function updateUI(data) {
    // 1. Update Alert Message
    const alertBox = document.getElementById('alert-box');
    const alertMessage = document.getElementById('alert-message');
    
    if (data.message) {
        alertMessage.textContent = `"${data.message}"`;
    } else {
        alertMessage.textContent = 'No immediate obstacles.';
    }

    // 2. Clear old bounding boxes
    const bboxOverlay = document.getElementById('bbox-overlay');
    bboxOverlay.innerHTML = '';

    // 3. Process Objects
    if (data.objects && data.objects.length > 0) {
        // Display stats for the highest priority object (assumed to be first)
        const primaryObj = data.objects[0];
        
        document.getElementById('val-object').textContent = (primaryObj.class || 'Unknown').toUpperCase();
        document.getElementById('val-confidence').textContent = primaryObj.confidence ? `${(primaryObj.confidence * 100).toFixed(0)}%` : '--';
        document.getElementById('val-position').textContent = (primaryObj.position || '--').toUpperCase();
        
        const angle = primaryObj.angle_deg || 0;
        document.getElementById('val-angle').textContent = `${Math.abs(angle)}° ${angle < 0 ? 'LEFT' : (angle > 0 ? 'RIGHT' : 'CENTER')}`;
        
        document.getElementById('val-distance').textContent = data.distance_m ? `${data.distance_m} m` : '--';
        document.getElementById('val-size').textContent = (primaryObj.estimated_size || '--').toUpperCase();
        
        const priority = (primaryObj.priority || 'low').toLowerCase();
        document.getElementById('val-priority').textContent = priority.toUpperCase();

        // Update alert box color based on priority
        alertBox.className = `alert-box ${priority}`;

        // 4. Draw bounding boxes for all objects in the response
        data.objects.forEach(obj => {
            if (obj.bbox && obj.bbox.length === 4) {
                drawBoundingBox(obj, bboxOverlay);
            }
        });
    } else {
        // Reset stats if no objects detected
        document.getElementById('val-object').textContent = 'NONE';
        document.getElementById('val-confidence').textContent = '--';
        document.getElementById('val-position').textContent = '--';
        document.getElementById('val-angle').textContent = '--';
        document.getElementById('val-distance').textContent = '--';
        document.getElementById('val-size').textContent = '--';
        document.getElementById('val-priority').textContent = 'NONE';
        alertBox.className = 'alert-box low';
    }
}

function drawBoundingBox(obj, overlay) {
    const [x1, y1, x2, y2] = obj.bbox;
    
    // Scale the bbox coordinates based on the actual rendered size of the camera container on screen
    const containerWidth = overlay.clientWidth;
    const containerHeight = overlay.clientHeight;
    
    const scaleX = containerWidth / CAMERA_WIDTH;
    const scaleY = containerHeight / CAMERA_HEIGHT;
    
    const boxLeft = x1 * scaleX;
    const boxTop = y1 * scaleY;
    const boxWidth = (x2 - x1) * scaleX;
    const boxHeight = (y2 - y1) * scaleY;

    // Create the box element
    const boxEl = document.createElement('div');
    boxEl.className = 'bounding-box';
    boxEl.style.left = `${boxLeft}px`;
    boxEl.style.top = `${boxTop}px`;
    boxEl.style.width = `${boxWidth}px`;
    boxEl.style.height = `${boxHeight}px`;

    // Priority color mapping for bbox
    const p = obj.priority ? obj.priority.toLowerCase() : 'low';
    let borderColor = 'var(--low-priority)';
    if (p === 'high') borderColor = 'var(--high-priority)';
    else if (p === 'medium') borderColor = 'var(--medium-priority)';
    
    boxEl.style.borderColor = borderColor;

    // Create the label element
    const labelEl = document.createElement('div');
    labelEl.className = 'bounding-box-label';
    labelEl.textContent = `${(obj.class || 'unknown').toUpperCase()}`;
    labelEl.style.backgroundColor = borderColor;

    boxEl.appendChild(labelEl);
    overlay.appendChild(boxEl);
}

// Start polling
setInterval(fetchLatestData, POLL_INTERVAL_MS);
fetchLatestData(); // initial fetch

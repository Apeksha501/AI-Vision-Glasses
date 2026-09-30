from fastapi import UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse 
from pathlib import Path
import shutil
import uuid

from ai.obstacle_detector import detector
from ai.decision_engine import assess_obstacle_risk

from datetime import datetime
from pathlib import Path
import json
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# APP CONFIGURATION
# ============================================================

APP_NAME = "AI Vision Glasses API"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=(
        "Temporary JSON-backed backend for the AI Vision Glasses "
        "smart vision assistance system."
    ),
    version=APP_VERSION,
)


# Allow the Flutter/mobile application to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# JSON DATABASE
# ============================================================

DEFAULT_DATA = {
    "users": [],
    "medicines": [],
    "reminders": [],
    "sensor_readings": [],
    "obstacle_events": [],
    "recognition_history": [],
}


def load_data():
    """Load application data from JSON file."""

    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA.copy())

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, FileNotFoundError):
        save_data(DEFAULT_DATA.copy())
        return DEFAULT_DATA.copy()


def save_data(data):
    """Save application data to JSON file."""

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def generate_id():
    """Generate a unique ID."""

    return str(uuid.uuid4())


def current_time():
    """Return current timestamp."""

    return datetime.now().isoformat()


# ============================================================
# PYDANTIC MODELS
# ============================================================

class UserCreate(BaseModel):
    name: str
    email: str


class MedicineCreate(BaseModel):
    name: str
    purpose: str = ""
    dosage: str = ""
    instructions: str = ""


class ReminderCreate(BaseModel):
    medicine_id: str
    time: str
    frequency: str = "daily"


class SensorReading(BaseModel):
    sensor_type: str
    distance_cm: float = Field(..., ge=0)
    value: float | None = None


class ObstacleEvent(BaseModel):
    object_name: str
    distance_cm: float = Field(..., ge=0)
    confidence: float = Field(..., ge=0, le=1)


class MedicineRecognition(BaseModel):
    medicine_name: str
    confidence: float = Field(..., ge=0, le=1)


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "message": "AI Vision Glasses API is running",
        "status": "success",
        "version": APP_VERSION,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "backend": "online",
        "storage": "JSON",
        "timestamp": current_time(),
    }


# ============================================================
# SYSTEM STATUS
# ============================================================

@app.get("/api/status")
def system_status():

    data = load_data()

    return {
        "system": "AI Vision Glasses",
        "backend": "online",
        "storage": "JSON",
        "users": len(data["users"]),
        "medicines": len(data["medicines"]),
        "reminders": len(data["reminders"]),
        "sensor_readings": len(data["sensor_readings"]),
        "obstacle_events": len(data["obstacle_events"]),
        "recognition_events": len(data["recognition_history"]),
        "timestamp": current_time(),
    }


# ============================================================
# USERS
# ============================================================

@app.post("/api/users")
def create_user(user: UserCreate):

    data = load_data()

    new_user = {
        "id": generate_id(),
        "name": user.name,
        "email": user.email,
        "created_at": current_time(),
    }

    data["users"].append(new_user)
    save_data(data)

    return {
        "message": "User created successfully",
        "user": new_user,
    }


@app.get("/api/users")
def get_users():

    data = load_data()

    return {
        "count": len(data["users"]),
        "users": data["users"],
    }


# ============================================================
# MEDICINES
# ============================================================

@app.post("/api/medicines")
def create_medicine(medicine: MedicineCreate):

    data = load_data()

    new_medicine = {
        "id": generate_id(),
        "name": medicine.name,
        "purpose": medicine.purpose,
        "dosage": medicine.dosage,
        "instructions": medicine.instructions,
        "created_at": current_time(),
    }

    data["medicines"].append(new_medicine)
    save_data(data)

    return {
        "message": "Medicine added successfully",
        "medicine": new_medicine,
    }


@app.get("/api/medicines")
def get_medicines():

    data = load_data()

    return {
        "count": len(data["medicines"]),
        "medicines": data["medicines"],
    }


@app.get("/api/medicines/{medicine_id}")
def get_medicine(medicine_id: str):

    data = load_data()

    for medicine in data["medicines"]:
        if medicine["id"] == medicine_id:
            return medicine

    raise HTTPException(
        status_code=404,
        detail="Medicine not found",
    )


# ============================================================
# MEDICINE REMINDERS
# ============================================================

@app.post("/api/reminders")
def create_reminder(reminder: ReminderCreate):

    data = load_data()

    medicine_exists = any(
        medicine["id"] == reminder.medicine_id
        for medicine in data["medicines"]
    )

    if not medicine_exists:
        raise HTTPException(
            status_code=404,
            detail="Medicine does not exist",
        )

    new_reminder = {
        "id": generate_id(),
        "medicine_id": reminder.medicine_id,
        "time": reminder.time,
        "frequency": reminder.frequency,
        "active": True,
        "created_at": current_time(),
    }

    data["reminders"].append(new_reminder)
    save_data(data)

    return {
        "message": "Reminder created successfully",
        "reminder": new_reminder,
    }


@app.get("/api/reminders")
def get_reminders():

    data = load_data()

    return {
        "count": len(data["reminders"]),
        "reminders": data["reminders"],
    }


# ============================================================
# SENSOR DATA
# ============================================================

@app.post("/api/sensors/readings")
def add_sensor_reading(reading: SensorReading):

    data = load_data()

    new_reading = {
        "id": generate_id(),
        "sensor_type": reading.sensor_type,
        "distance_cm": reading.distance_cm,
        "value": reading.value,
        "timestamp": current_time(),
    }

    data["sensor_readings"].append(new_reading)

    # Keep JSON storage from growing indefinitely during testing
    if len(data["sensor_readings"]) > 1000:
        data["sensor_readings"] = data["sensor_readings"][-1000:]

    save_data(data)

    return {
        "message": "Sensor reading stored",
        "reading": new_reading,
    }


@app.get("/api/sensors/readings")
def get_sensor_readings():

    data = load_data()

    return {
        "count": len(data["sensor_readings"]),
        "readings": data["sensor_readings"],
    }


# ============================================================
# OBSTACLE DETECTION
# ============================================================

@app.post("/api/obstacles")
def add_obstacle_event(obstacle: ObstacleEvent):

    data = load_data()

    # Simple alert classification based on distance
    if obstacle.distance_cm <= 50:
        alert_level = "danger"
    elif obstacle.distance_cm <= 100:
        alert_level = "warning"
    else:
        alert_level = "safe"

    new_event = {
        "id": generate_id(),
        "object_name": obstacle.object_name,
        "distance_cm": obstacle.distance_cm,
        "confidence": obstacle.confidence,
        "alert_level": alert_level,
        "timestamp": current_time(),
    }

    data["obstacle_events"].append(new_event)

    if len(data["obstacle_events"]) > 1000:
        data["obstacle_events"] = data["obstacle_events"][-1000:]

    save_data(data)

    return {
        "message": "Obstacle event recorded",
        "event": new_event,
    }


@app.get("/api/obstacles")
def get_obstacles():

    data = load_data()

    return {
        "count": len(data["obstacle_events"]),
        "events": data["obstacle_events"],
    }


# ============================================================
# MEDICINE RECOGNITION
# ============================================================

@app.post("/api/medicine/recognize")
def recognize_medicine(recognition: MedicineRecognition):

    data = load_data()

    # IMPORTANT:
    # This endpoint is currently a backend integration endpoint.
    # The real trained AI model will be connected here later.

    if recognition.confidence >= 0.80:
        verification_status = "high_confidence"
    elif recognition.confidence >= 0.50:
        verification_status = "verify_result"
    else:
        verification_status = "low_confidence"

    result = {
        "id": generate_id(),
        "medicine_name": recognition.medicine_name,
        "confidence": recognition.confidence,
        "verification_status": verification_status,
        "timestamp": current_time(),
    }

    data["recognition_history"].append(result)

    if len(data["recognition_history"]) > 1000:
        data["recognition_history"] = data["recognition_history"][-1000:]

    save_data(data)

    return {
        "message": "Medicine recognition result recorded",
        "result": result,
    }


@app.get("/api/medicine/history")
def get_recognition_history():

    data = load_data()

    return {
        "count": len(data["recognition_history"]),
        "history": data["recognition_history"],
    }


# ============================================================
# COMBINED DASHBOARD DATA
# ============================================================

@app.get("/api/dashboard")
def dashboard():

    data = load_data()

    return {
        "system": {
            "name": "AI Vision Glasses",
            "status": "online",
            "timestamp": current_time(),
        },
        "statistics": {
            "users": len(data["users"]),
            "medicines": len(data["medicines"]),
            "reminders": len(data["reminders"]),
            "sensor_readings": len(data["sensor_readings"]),
            "obstacle_events": len(data["obstacle_events"]),
            "recognition_events": len(data["recognition_history"]),
        },
        "latest_sensor_reading": (
            data["sensor_readings"][-1]
            if data["sensor_readings"]
            else None
        ),
        "latest_obstacle": (
            data["obstacle_events"][-1]
            if data["obstacle_events"]
            else None
        ),
        "latest_recognition": (
            data["recognition_history"][-1]
            if data["recognition_history"]
            else None
        ),
    }
@app.post("/api/ai/detect-obstacles")
async def detect_obstacles(file: UploadFile = File(...)):

    # Create temporary upload directory
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    # Create unique filename
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}_{file.filename}"

    # Save uploaded image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:

        # Run YOLO
        detections = detector.detect(str(file_path))

        risk_assessment = assess_obstacle_risk(
            detections=detections
        )

        return {
            "status": "success",
            "model": "YOLO11n",
            "detections": detections,
            "obstacle_count": len(detections),
            "risk_assessment": risk_assessment
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.post("/api/ai/assist")
async def ai_assistance(
    file: UploadFile = File(...),
    distance_cm: float = 35
):
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:

        # Step 1: Detect objects using YOLO
        detections = detector.detect(str(file_path))

        # Step 2: Combine AI detection with sensor distance
        risk_assessment = assess_obstacle_risk(
            detections=detections,
            distance_cm=distance_cm
        )

        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "distance_cm": distance_cm,
            "detections": detections,
            "risk_level": risk_assessment["risk_level"],
            "voice_message": risk_assessment["voice_message"]
        }

        data = load_data()

        data.setdefault("obstacle_events", []).append(event)

        save_data(data)

        return {
            "status": "success",
            "system": "AI Vision Glasses",
            "ai_model": "YOLO11n",
            "sensor": {
                "type": "ultrasonic",
                "distance_cm": distance_cm
            },
            "detections": detections,
            "risk_assessment": risk_assessment,
            "event_id": event["id"]
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():

    dashboard_path = Path("dashboard/index.html")

    return dashboard_path.read_text()
@app.post("/api/medicine/demo-recognize")
async def demo_medicine_recognition(
    file: UploadFile = File(...)
):
    return {
        "status": "success",
        "mode": "prototype",
        "message": "Medicine recognition module is connected.",
        "medicine": "Demo Medicine",
        "confidence": 0.90,
        "verification_required": True,
        "note": "This is a software prototype. Medicine identity must be verified before use."
    }
@app.get("/api/ai/history")
async def ai_detection_history():

    data = load_data()

    return {
        "status": "success",
        "count": len(data.get("obstacle_events", [])),
        "history": data.get("obstacle_events", [])
    }
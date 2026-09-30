from ultralytics import YOLO


class ObstacleDetector:

    def __init__(self):
        print("Loading YOLO model...")
        self.model = YOLO("yolo11n.pt")
        print("YOLO model loaded successfully.")

    def detect(self, image_path):

        results = self.model(image_path)

        detections = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                class_name = self.model.names[class_id]

                coordinates = box.xyxy[0].tolist()

                detections.append({
                    "object": class_name,
                    "confidence": round(confidence, 3),
                    "bounding_box": {
                        "x1": round(coordinates[0], 2),
                        "y1": round(coordinates[1], 2),
                        "x2": round(coordinates[2], 2),
                        "y2": round(coordinates[3], 2)
                    }
                })

        return detections


detector = ObstacleDetector()
def assess_obstacle_risk(detections, distance_cm=None):

    if not detections:
        return {
            "risk_level": "LOW",
            "alert": "No obstacle detected.",
            "voice_message": "Path appears clear."
        }

    highest_confidence = max(
        detection["confidence"]
        for detection in detections
    )

    objects = [
        detection["object"]
        for detection in detections
    ]

    # If sensor distance is available
    if distance_cm is not None:

        if distance_cm <= 50:
            risk_level = "HIGH"
            voice_message = "Obstacle detected very close."
        
        elif distance_cm <= 150:
            risk_level = "MEDIUM"
            voice_message = "Obstacle detected nearby."
        
        else:
            risk_level = "LOW"
            voice_message = "Obstacle detected at a safe distance."

    else:
        # AI-only fallback when sensor data isn't available
        if highest_confidence >= 0.80:
            risk_level = "MEDIUM"
            voice_message = "Obstacle detected ahead."
        else:
            risk_level = "LOW"
            voice_message = "Possible obstacle detected."

    return {
        "risk_level": risk_level,
        "detected_objects": objects,
        "highest_confidence": round(highest_confidence, 3),
        "distance_cm": distance_cm,
        "alert": f"{risk_level} risk obstacle detected.",
        "voice_message": voice_message
    }
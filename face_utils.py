from deepface import DeepFace
import os

def compare_faces(img1_path, img2_path):
    try:
        # ✅ Check files exist
        if not os.path.exists(img1_path):
            return {"error": "Missing person image not found"}
        
        if not os.path.exists(img2_path):
            return {"error": "Police verification image not found"}

        # 🔥 DeepFace verification
        result = DeepFace.verify(
            img1_path=img1_path,
            img2_path=img2_path,
            enforce_detection=False  # prevents crash if face not detected
        )

        # ✅ Extract values
        distance = result.get("distance", 1.0)
        match = result.get("verified", False)

        # ✅ Convert to confidence %
        confidence = max(0, min(100, int((1 - distance) * 100)))

        return {
            "match": match,
            "confidence": confidence,
            "distance": float(distance)
        }

    except Exception as e:
        return {"error": str(e)}
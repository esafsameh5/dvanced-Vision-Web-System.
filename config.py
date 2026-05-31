import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
KNOWN_FACES_DIR = os.path.join(DATA_DIR, "known_faces")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "face_embeddings.json")
CUSTOM_GESTURES_FILE = os.path.join(DATA_DIR, "custom_gestures.json")
UNKNOWN_FACES_DIR = os.path.join(DATA_DIR, "unknown_faces")

CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", "960"))
FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", "540"))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "82"))

FACE_CONFIDENCE = float(os.getenv("FACE_CONFIDENCE", "0.60"))
HAND_CONFIDENCE = float(os.getenv("HAND_CONFIDENCE", "0.70"))
FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.32"))
FACE_RECOGNITION_EVERY_N_FRAMES = int(os.getenv("FACE_RECOGNITION_EVERY_N_FRAMES", "10"))

DEEPFACE_MODEL = os.getenv("DEEPFACE_MODEL", "Facenet512")
DEEPFACE_DETECTOR_BACKEND = os.getenv("DEEPFACE_DETECTOR_BACKEND", "skip")

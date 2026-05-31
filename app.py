import os
import sys
import threading
import time
import uuid
import queue
from typing import Dict, Optional, Tuple

import cv2
import mediapipe as mp
from flask import Flask, Response, jsonify, render_template, request

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from config import (
    CAMERA_INDEX,
    FACE_CONFIDENCE,
    FACE_MATCH_THRESHOLD,
    FACE_RECOGNITION_EVERY_N_FRAMES,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    HAND_CONFIDENCE,
    JPEG_QUALITY,
    UNKNOWN_FACES_DIR,
)
from src.face_db import FaceDatabase
from src.hand_utils import add_custom_gesture, delete_custom_gesture, hand_payload, load_custom_gestures

app = Flask(__name__)

mp_face_detection = mp.solutions.face_detection
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

face_db = FaceDatabase()
state_lock = threading.Lock()
unknown_lock = threading.Lock()
unknown_faces: Dict[str, Dict] = {}
latest_state: Dict = {
    "faces": [],
    "face": "No Face",
    "face_distance": None,
    "unknown_available": False,
    "unknown_faces": [],
    "hands": [],
    "people": face_db.list_people(),
    "custom_gestures": load_custom_gestures(),
    "frame": {"width": FRAME_WIDTH, "height": FRAME_HEIGHT},
}


class CameraProcessor:
    def __init__(self) -> None:
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera. Change CAMERA_INDEX or check camera permissions.")
        self.face_detector = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=FACE_CONFIDENCE)
        self.hands_detector = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=HAND_CONFIDENCE,
            min_tracking_confidence=HAND_CONFIDENCE,
        )
        self.frame_no = 0
        self.last_faces = []
        self.tracked_faces = {}
        self.next_track_id = 0
        self.recognition_queue = queue.Queue(maxsize=1)
        self.recognition_thread = threading.Thread(target=self._recognition_worker, daemon=True)
        self.recognition_thread.start()

    @staticmethod
    def _safe_box(relative_box, width: int, height: int) -> Tuple[int, int, int, int]:
        x = int(relative_box.xmin * width)
        y = int(relative_box.ymin * height)
        w = int(relative_box.width * width)
        h = int(relative_box.height * height)
        pad_x = int(w * 0.18)
        pad_y = int(h * 0.25)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(width, x + w + pad_x)
        y2 = min(height, y + h + pad_y)
        return x1, y1, x2, y2

    @staticmethod
    def _box_center(box: Tuple[int, int, int, int]) -> Tuple[float, float]:
        x1, y1, x2, y2 = box
        return (x1 + x2) / 2, (y1 + y2) / 2

    @staticmethod
    def _remember_unknown(face_crop, box, distance: float) -> str:
        os.makedirs(UNKNOWN_FACES_DIR, exist_ok=True)
        unknown_id = str(uuid.uuid4())[:8]
        file_path = os.path.join(UNKNOWN_FACES_DIR, f"{unknown_id}.jpg")
        cv2.imwrite(file_path, face_crop)
        with unknown_lock:
            # Keep only the latest 12 unknown snapshots.
            unknown_faces[unknown_id] = {
                "id": unknown_id,
                "crop": face_crop,
                "box": box,
                "distance": distance,
                "created_at": time.time(),
            }
            if len(unknown_faces) > 12:
                oldest = sorted(unknown_faces.values(), key=lambda item: item["created_at"])[0]["id"]
                unknown_faces.pop(oldest, None)
        return unknown_id

    def _recognition_worker(self):
        while True:
            track_id = None
            try:
                track_id, face_crop, box = self.recognition_queue.get()
                if face_crop is not None and face_crop.size > 0:
                    label, distance = face_db.recognize(face_crop, FACE_MATCH_THRESHOLD)
                    unknown_id = None
                    if label == "Unknown Face":
                        unknown_id = CameraProcessor._remember_unknown(face_crop, box, distance)
                    
                    with state_lock:
                        if track_id in self.tracked_faces:
                            self.tracked_faces[track_id].update({
                                "name": label,
                                "distance": distance,
                                "id": unknown_id,
                                "unknown": label == "Unknown Face",
                                "is_processing": False,
                                "last_recognition_time": time.time()
                            })
                else:
                    with state_lock:
                        if track_id in self.tracked_faces:
                            self.tracked_faces[track_id]["is_processing"] = False
                self.recognition_queue.task_done()
            except Exception as e:
                print(f"[CameraProcessor] Recognition worker error: {e}")
                if track_id is not None:
                    with state_lock:
                        if track_id in self.tracked_faces:
                            self.tracked_faces[track_id]["is_processing"] = False
                            self.tracked_faces[track_id]["name"] = "Detection Error"
                try:
                    self.recognition_queue.task_done()
                except Exception:
                    pass
                time.sleep(0.5)

    def _recognize_faces(self, detections, frame, width: int, height: int):
        current_detections = []
        for idx, detection in enumerate(detections):
            box = self._safe_box(detection.location_data.relative_bounding_box, width, height)
            center = self._box_center(box)
            current_detections.append({
                "box": box,
                "center": center,
                "detection": detection
            })

        matched_indices = set()
        updated_tracked_faces = {}
        
        for det in current_detections:
            best_track_id = None
            best_dist = 120.0
            
            for track_id, tf in self.tracked_faces.items():
                tx, ty = tf["center"]
                cx, cy = det["center"]
                dist = ((tx - cx)**2 + (ty - cy)**2)**0.5
                if dist < best_dist:
                    best_dist = dist
                    best_track_id = track_id
            
            if best_track_id is not None and best_track_id not in matched_indices:
                matched_indices.add(best_track_id)
                tf = self.tracked_faces[best_track_id]
                x1, y1, x2, y2 = det["box"]
                face_crop = frame[y1:y2, x1:x2].copy()
                
                updated_tracked_faces[best_track_id] = {
                    "center": det["center"],
                    "box": det["box"],
                    "name": tf["name"],
                    "distance": tf["distance"],
                    "id": tf["id"],
                    "unknown": tf["unknown"],
                    "is_processing": tf["is_processing"],
                    "last_recognition_time": tf.get("last_recognition_time", 0.0),
                    "last_seen": self.frame_no,
                    "crop": face_crop
                }
            else:
                x1, y1, x2, y2 = det["box"]
                face_crop = frame[y1:y2, x1:x2].copy()
                track_id = self.next_track_id
                self.next_track_id += 1
                
                updated_tracked_faces[track_id] = {
                    "center": det["center"],
                    "box": det["box"],
                    "name": "Detecting...",
                    "distance": None,
                    "id": None,
                    "unknown": False,
                    "is_processing": False,
                    "last_recognition_time": 0.0,
                    "last_seen": self.frame_no,
                    "crop": face_crop
                }

        for track_id, tf in self.tracked_faces.items():
            if track_id not in matched_indices and (self.frame_no - tf["last_seen"] < 8):
                updated_tracked_faces[track_id] = tf

        self.tracked_faces = updated_tracked_faces

        now = time.time()
        for track_id, tf in self.tracked_faces.items():
            needs_recognition = not tf["is_processing"] and (
                tf["name"] == "Detecting..." or 
                (tf["name"] == "Unknown Face" and now - tf["last_recognition_time"] > 8.0) or
                (tf["name"] != "Detecting..." and tf["name"] != "Unknown Face" and now - tf["last_recognition_time"] > 15.0)
            )
            
            if needs_recognition:
                try:
                    tf["is_processing"] = True
                    self.recognition_queue.put_nowait((track_id, tf["crop"], tf["box"]))
                except queue.Full:
                    tf["is_processing"] = False

        faces_payload = []
        for idx, (track_id, tf) in enumerate(self.tracked_faces.items()):
            if tf["last_seen"] == self.frame_no:
                x1, y1, x2, y2 = tf["box"]
                faces_payload.append({
                    "index": idx + 1,
                    "id": tf["id"],
                    "name": tf["name"],
                    "distance": tf["distance"],
                    "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "center": tf["center"],
                    "unknown": tf["unknown"] or tf["name"] == "Unknown Face",
                })
        
        self.last_faces = faces_payload
        return faces_payload

    def read_annotated_frame(self):
        ok, frame = self.cap.read()
        if not ok:
            return None
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]
        self.frame_no += 1

        faces_payload = []
        face_results = self.face_detector.process(rgb)
        if face_results.detections:
            faces_payload = self._recognize_faces(face_results.detections, frame, width, height)
            for face in faces_payload:
                box = face["box"]
                color = (0, 200, 0) if not face["unknown"] else (0, 0, 255)
                cv2.rectangle(frame, (box["x1"], box["y1"]), (box["x2"], box["y2"]), color, 2)
                dist = face.get("distance")
                label = face["name"] if dist is None else f"{face['name']} ({dist:.2f})"
                cv2.putText(frame, label, (box["x1"], max(30, box["y1"] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.72, color, 2)
        else:
            self.last_faces = []

        hands_payload = []
        hand_results = self.hands_detector.process(rgb)
        if hand_results.multi_hand_landmarks:
            handedness_list = hand_results.multi_handedness or []
            for idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                handedness = "Right"
                if idx < len(handedness_list):
                    handedness = handedness_list[idx].classification[0].label
                payload = hand_payload(hand_landmarks, handedness)
                hands_payload.append(payload)
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )
                wrist = hand_landmarks.landmark[0]
                tx, ty = int(wrist.x * width), int(wrist.y * height)
                pinch = "PINCH" if payload["pinch"]["active"] else "OPEN"
                cv2.putText(frame, f"{handedness}: {payload['fingers']} - {payload['gesture']} - {pinch}", (tx, max(30, ty - 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 170, 0), 2)

        first_face = faces_payload[0] if faces_payload else None
        with state_lock:
            latest_state.update({
                "faces": faces_payload,
                "face": first_face["name"] if first_face else "No Face",
                "face_distance": first_face.get("distance") if first_face else None,
                "unknown_available": any(f["unknown"] for f in faces_payload),
                "unknown_faces": [
                    {"id": f["id"], "distance": f["distance"], "box": f["box"]}
                    for f in faces_payload if f.get("id")
                ],
                "hands": hands_payload,
                "people": face_db.list_people(),
                "custom_gestures": load_custom_gestures(),
                "frame": {"width": width, "height": height},
                "time": time.time(),
            })
        return frame

    def release(self) -> None:
        self.cap.release()
        self.face_detector.close()
        self.hands_detector.close()


camera: Optional[CameraProcessor] = None


def get_camera() -> CameraProcessor:
    global camera
    if camera is None:
        camera = CameraProcessor()
    return camera


def generate_frames():
    cam = get_camera()
    while True:
        frame = cam.read_annotated_frame()
        if frame is None:
            continue
        ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        if not ok:
            continue
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/state")
def api_state():
    with state_lock:
        return jsonify(latest_state)


@app.route("/api/register_face", methods=["POST"])
def api_register_face():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    unknown_id = (payload.get("unknown_id") or "").strip()
    if not name:
        return jsonify({"ok": False, "message": "Person name is required."}), 400
    with unknown_lock:
        if unknown_id:
            item = unknown_faces.get(unknown_id)
        else:
            item = sorted(unknown_faces.values(), key=lambda v: v["created_at"], reverse=True)[0] if unknown_faces else None
    if not item:
        return jsonify({"ok": False, "message": "No unknown face snapshot is available."}), 400
    ok = face_db.add_person_image(name, item["crop"])
    if not ok:
        return jsonify({"ok": False, "message": "Failed to register face. Move closer and try again."}), 500
    return jsonify({"ok": True, "message": f"{name} registered successfully.", "people": face_db.list_people()})


@app.route("/api/add_face_sample", methods=["POST"])
def api_add_face_sample():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    unknown_id = (payload.get("unknown_id") or "").strip()
    if not name:
        return jsonify({"ok": False, "message": "Select a person first."}), 400
    with unknown_lock:
        item = unknown_faces.get(unknown_id) if unknown_id else None
        if item is None and unknown_faces:
            item = sorted(unknown_faces.values(), key=lambda v: v["created_at"], reverse=True)[0]
    if not item:
        return jsonify({"ok": False, "message": "No face snapshot is available."}), 400
    ok = face_db.add_person_image(name, item["crop"])
    if not ok:
        return jsonify({"ok": False, "message": "Failed to add sample."}), 500
    return jsonify({"ok": True, "message": "Sample added successfully.", "people": face_db.list_people()})


@app.route("/api/rename_person", methods=["POST"])
def api_rename_person():
    payload = request.get_json(silent=True) or {}
    ok, message = face_db.rename_person(payload.get("old_name", ""), payload.get("new_name", ""))
    return jsonify({"ok": ok, "message": message, "people": face_db.list_people()}), (200 if ok else 400)


@app.route("/api/delete_person", methods=["POST"])
def api_delete_person():
    payload = request.get_json(silent=True) or {}
    ok, message = face_db.delete_person(payload.get("name", ""))
    return jsonify({"ok": ok, "message": message, "people": face_db.list_people()}), (200 if ok else 400)


@app.route("/api/clear_samples", methods=["POST"])
def api_clear_samples():
    payload = request.get_json(silent=True) or {}
    ok, message = face_db.clear_samples(payload.get("name", ""))
    return jsonify({"ok": ok, "message": message, "people": face_db.list_people()}), (200 if ok else 400)


@app.route("/api/custom_gestures", methods=["GET", "POST", "DELETE"])
def api_custom_gestures():
    if request.method == "GET":
        return jsonify({"gestures": load_custom_gestures()})
    payload = request.get_json(silent=True) or {}
    if request.method == "POST":
        ok, message, gestures = add_custom_gesture(payload.get("name", ""), payload.get("states", {}))
    else:
        name = payload.get("name", "") or request.args.get("name", "")
        print(f"[DEBUG] DELETE received name: '{name}', type: {type(name)}")
        ok, message, gestures = delete_custom_gesture(name)
        print(f"[DEBUG] DELETE result: ok={ok}, message='{message}'")
    return jsonify({"ok": ok, "message": message, "gestures": gestures}), (200 if ok else 400)


@app.route("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
    finally:
        if camera is not None:
            camera.release()

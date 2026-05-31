# 🎥 Advanced Vision Web System

A powerful Flask + MediaPipe web application for real-time computer vision tasks with advanced face recognition, hand gesture detection, and interactive hand-controlled features.

## ✨ Core Features

### 👤 Face Recognition & Management
- **Multi-face detection** - Detect multiple faces in the same camera frame simultaneously
- **Face recognition** - Identify registered people using DeepFace embeddings (Facenet512)
- **Unknown face detection** - Automatically detect and display unknown faces
- **Face registration** - Register new people by providing name and sample
- **Face management**:
  - Rename registered people
  - Delete person records
  - Clear face samples
  - Add additional samples for better recognition
  - View all registered people
- **Face embeddings** - Automatic DeepFace embedding generation and storage (face_embeddings.json)

### ✋ Hand Gesture & Interaction
- **Real-time hand detection** - Detect up to 2 hands simultaneously
- **Hand analytics**:
  - Hand side identification (Left/Right)
  - Finger count (0-5)
  - Finger state analysis (open/closed per finger)
  - Pinch detection and tracking
- **Custom gesture creation** - Define custom gestures based on finger states
- **Gesture recognition** - Identify custom-defined hand gestures in real-time

### 🎨 Hand-Controlled Drawing & Writing
- **Draw mode** - Create freehand drawings using hand gestures
  - Activate: Bring thumb and index finger together (pinch)
  - Draw: Move index finger while pinching
  - Stop: Release the pinch
- **Write mode** - Write text using hand gestures with visual feedback
- **Interactive overlay** - Real-time visual feedback on video stream

### 📝 Word & Text Manipulation
- **Add words/sentences** - Input text to be displayed on canvas
- **Move words** - Grab and reposition text using hand gestures
- **Drag and drop** - Pinch to grab, move to drag, open fingers to drop
- **Interactive text control** - Full hand-controlled text management

### ⚙️ Custom Gesture Rules
- **Create gestures** - Define gestures from finger combinations
- **Example gesture** - "Pointing" (Thumb closed, Index open, others closed)
- **Save & reuse** - Store custom gestures in custom_gestures.json
- **Real-time recognition** - Instantly recognize defined gestures

## 📋 Requirements

- **OS**: Windows 10/11
- **Python**: 3.10, 3.11, or 3.12
- **Webcam**: USB or built-in camera with at least 720p resolution
- **RAM**: Minimum 4GB (8GB recommended for smooth performance)

## 📦 Dependencies

The project uses the following key libraries:

```
Flask 3.0.3              - Web framework
MediaPipe 0.10.14        - Vision ML library (hand & face detection)
OpenCV 4.10.0.84         - Computer vision processing
DeepFace 0.0.95          - Face recognition & embedding
TensorFlow 2.16.1        - ML backend
NumPy 1.26.4             - Numerical computing
Pillow 10.4.0            - Image processing
```

## Install

Open PowerShell inside the project folder:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you previously installed conflicting TensorFlow versions globally, use a new virtual environment. This project pins `tensorflow==2.16.1`, `tf-keras==2.16.0`, and `protobuf==4.25.3` to stay compatible with MediaPipe.

## Run

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Camera index

If your camera does not open, try another index:

```powershell
set CAMERA_INDEX=1
python app.py
```

## 🎯 Usage Guide

### Face Recognition Workflow

1. **Show faces to camera**
   - Position your face in front of the webcam
   - Multiple faces are detected simultaneously

2. **Unknown face detection**
   - Unknown faces appear in the **Unknown Faces** panel on the right
   - Each unknown face gets a temporary ID (e.g., "Unknown_xyz")
   - Unknown faces are automatically saved in `data/unknown_faces/`

3. **Register new person**
   - Select an unknown face from the dropdown
   - Enter the person's name in the text field
   - Click **Register Selected Unknown Face**
   - Face embedding is automatically generated and saved

4. **Manage registered people**
   - **Rename**: Change the name of a registered person
   - **Delete**: Remove person and all their face samples
   - **Clear Samples**: Remove all stored face samples for a person
   - **Add Sample**: Capture a new face sample from current unknown face
   - All changes are reflected in `face_embeddings.json`

5. **Improve recognition**
   - Add 3-5 samples per person for best accuracy
   - Use different angles and lighting conditions
   - Clear samples if recognition becomes poor

### Hand Gesture Detection

1. **Show your hand to the camera**
   - Both left and right hands are detected simultaneously

2. **View hand information**
   - **Hand side**: Displays whether it's left or right hand
   - **Finger count**: Shows number of open fingers (0-5)
   - **Finger states**: Individual state for each finger (thumb, index, middle, ring, pinky)
   - **Gesture name**: Custom gesture if matched
   - **Pinch status**: Shows if pinch is active (thumb + index touching)

### Drawing & Writing with Hand Gestures

#### Draw Mode
1. Select **Draw** from the mode dropdown
2. Position your hand in front of camera
3. **Activate drawing**: Bring thumb and index finger together (pinch gesture)
4. **Draw**: Move your index finger while maintaining pinch - leaves a trail on screen
5. **Stop drawing**: Open your fingers to release the pinch
6. Drawing appears as overlay on video stream

#### Write Mode
1. Select **Write** from the mode dropdown
2. Position your hand for comfortable writing position
3. Follow same pinch gesture as draw mode
4. Move your hand to write letters and words
5. Real-time text visualization with hand coordinates

**Tips:**
- Keep hand steady while pinching
- Slow, deliberate movements produce cleaner results
- Adequate lighting improves hand detection accuracy

### Interactive Word & Text Control

1. **Add text**
   - Type a word or sentence in the input field below camera
   - Click **Add Word** button
   - Text appears on the video overlay

2. **Move words**
   - Select **Move Words** mode from dropdown
   - Position hand near a word to grab it
   - **Pinch near word**: Use thumb + index pinch gesture
   - **Drag**: Keep pinching and move hand to desired position
   - **Drop**: Open all fingers to release the word
   
3. **Multiple words**
   - Add multiple words/sentences for more interactive gameplay
   - Control each word independently with separate pinch gestures
   - Words remain on screen until cleared

**Advanced Features:**
- Real-time position tracking
- Smooth hand-to-word mapping
- Visual feedback during grab/drag/drop operations

### Custom Gesture Creation & Recognition

#### Creating a Custom Gesture

1. Go to **Custom Gesture Rules** section
2. For each finger (Thumb, Index, Middle, Ring, Pinky), select state:
   - **Open**: Finger is extended
   - **Closed**: Finger is curled
3. Enter gesture name (e.g., "Pointing", "OK Sign", "Peace")
4. Click **Save Gesture**
5. Gesture is stored in `custom_gestures.json`

#### Example Gestures

**Pointing Gesture**
| Finger | State |
|--------|-------|
| Thumb  | Closed |
| Index  | Open |
| Middle | Closed |
| Ring   | Closed |
| Pinky  | Closed |

**OK Sign Gesture**
| Finger | State |
|--------|-------|
| Thumb  | Open |
| Index  | Closed |
| Middle | Open |
| Ring   | Open |
| Pinky  | Open |

#### Gesture Recognition
- Once saved, custom gestures are recognized in real-time
- **Gesture name** displays when your hand matches the defined pattern
- Use custom gestures to trigger application actions or create interactive experiences

## 🔧 Configuration

Edit `config.py` to customize behavior:

```python
CAMERA_INDEX = 0              # Webcam index (0 for default)
FRAME_WIDTH = 960             # Video frame width
FRAME_HEIGHT = 540            # Video frame height
FACE_CONFIDENCE = 0.60        # Face detection threshold (0-1)
HAND_CONFIDENCE = 0.70        # Hand detection threshold (0-1)
FACE_MATCH_THRESHOLD = 0.32   # Face recognition similarity threshold
FACE_RECOGNITION_EVERY_N_FRAMES = 10  # Process every N frames for performance
DEEPFACE_MODEL = "Facenet512" # Face embedding model
JPEG_QUALITY = 82             # Video stream compression quality
```

### Environment Variables

```powershell
# Override config.py values
$env:CAMERA_INDEX = "1"
$env:FACE_CONFIDENCE = "0.70"
$env:HAND_CONFIDENCE = "0.75"
$env:FACE_MATCH_THRESHOLD = "0.30"
```

## 📁 Project Structure

```text
mediapipe_flask_vision_studio/
├── app.py                          # Main Flask application & camera processing
├── config.py                       # Configuration & environment variables
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── src/
│   ├── face_db.py                 # Face database management & DeepFace integration
│   └── hand_utils.py              # Hand detection utilities & gesture handling
│
├── templates/
│   └── index.html                 # Main web interface
│
├── static/
│   ├── css/
│   │   └── style.css              # Styling
│   └── js/
│       ├── app.js                 # Main application logic
│       └── app_v2.js              # Alternative/updated logic
│
└── data/
    ├── known_faces/               # Registered person face samples (empty by default)
    ├── unknown_faces/             # Automatically saved unknown faces
    ├── face_embeddings.json        # DeepFace embeddings (auto-generated)
    └── custom_gestures.json        # Custom gesture definitions (auto-generated)
```

## 💡 Best Practices & Tips

### Face Recognition
- **Multiple samples**: Add 3-5 face samples per person for improved accuracy
- **Lighting**: Ensure good, consistent lighting for best results
- **Face crop**: Keep face centered and front-facing in frame
- **Distance**: Maintain 30-60cm distance from camera
- **Angle variety**: Add samples from different angles for robustness

### Hand Gesture Detection  
- **Hand visibility**: Keep entire hand visible in frame
- **Lighting**: Bright, uniform lighting improves detection
- **Background**: Contrasting background helps hand tracking
- **Pinch precision**: Practice smooth thumb-index finger movement
- **Gesture matching**: Ensure clear finger positions when creating gestures

### Performance Optimization
- Adjust `FACE_RECOGNITION_EVERY_N_FRAMES` to skip frames if needed
- Reduce frame resolution if experiencing lag
- Lower confidence thresholds to be more permissive
- Close unnecessary browser tabs to free memory

### Troubleshooting

**Camera not opening:**
- Check camera permissions in Windows settings
- Try different CAMERA_INDEX (0, 1, 2, etc.)
- Ensure no other application is using the camera

**Face recognition not working:**
- Add more face samples (at least 3-5 per person)
- Check lighting and face visibility
- Lower `FACE_MATCH_THRESHOLD` value (more permissive)
- Verify face_embeddings.json is being created

**Hand detection issues:**
- Ensure hand is fully visible in frame
- Improve lighting conditions
- Lower `HAND_CONFIDENCE` threshold
- Use gestures with clear, distinct finger positions

## 📚 API Endpoints

The Flask backend provides RESTful API endpoints for all operations:

- `GET /` - Main web interface
- `GET /video_feed` - WebRTC video stream
- `GET /api/state` - Current system state (faces, hands, people)
- `POST /api/register_unknown` - Register unknown face
- `POST /api/rename_person` - Rename registered person
- `POST /api/delete_person` - Delete registered person
- `POST /api/clear_samples` - Clear face samples
- `POST /api/add_gesture` - Add custom gesture
- `POST /api/delete_gesture` - Delete custom gesture

## 🔬 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Web Framework** | Flask | 3.0.3 |
| **Vision ML** | MediaPipe | 0.10.14 |
| **Computer Vision** | OpenCV | 4.10.0.84 |
| **Face Recognition** | DeepFace | 0.0.95 |
| **Machine Learning** | TensorFlow | 2.16.1 |
| **ML Backend** | Keras | 2.16.0 |
| **Image Processing** | Pillow | 10.4.0 |
| **Numerical Computing** | NumPy | 1.26.4 |

## 📝 License

This project is provided as-is for educational and research purposes.

## 👨‍💻 Authors

- **Esaf Sameh** - Project creator and maintainer

## 🤝 Contributing

Feel free to fork, modify, and submit improvements. Report issues and suggest features through GitHub Issues.

## ✅ Tested On

- Windows 11 with Python 3.12
- USB Logitech webcams
- Built-in laptop cameras
- Multiple concurrent users tested successfully

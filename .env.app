# Stamp Collection Toolset - Application Defaults
# Copy to .env.keys for secrets, .env.local for user overrides

# =============================================================================
# Database
# =============================================================================
DATABASE_PATH=data/stamps.db

# =============================================================================
# Scraping Settings
# =============================================================================
SCRAPE_DELAY_SECONDS=1.5
SCRAPE_RETRY_COUNT=3
SCRAPE_RETRY_DELAY=5.0
SCRAPE_RETRY_BACKOFF=2.0
SCRAPE_ERROR_BEHAVIOR=skip

# Browser settings
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=60000

# =============================================================================
# RAG Settings
# =============================================================================
RAG_MATCH_AUTO_THRESHOLD=0.9
RAG_MATCH_MIN_THRESHOLD=0.5
EMBEDDING_MODEL=text-embedding-3-small

# =============================================================================
# Vision Settings (Groq)
# =============================================================================
GROQ_MODEL=llama-3.2-11b-vision-preview
GROQ_RATE_LIMIT_PER_MINUTE=30
VISION_PROMPT_PATH=config/llava_prompt.txt

# =============================================================================
# Detection Settings (Two-Stage Pipeline)
# =============================================================================

# Stage 1A: Polygon Detection
DETECTION_MODE=album
DETECTION_MIN_VERTICES=3
DETECTION_MAX_VERTICES=4
DETECTION_MIN_AREA_RATIO=0.001
DETECTION_MAX_AREA_RATIO=0.15
DETECTION_ASPECT_RATIO_MIN=0.3
DETECTION_ASPECT_RATIO_MAX=3.0
DETECTION_APPROX_EPSILON=0.02

# Stage 1B: Stamp Classifier
CLASSIFIER_MODE=heuristic
CLASSIFIER_CONFIDENCE_THRESHOLD=0.6
CLASSIFIER_COLOR_VARIANCE_WEIGHT=0.35
CLASSIFIER_EDGE_COMPLEXITY_WEIGHT=0.30
CLASSIFIER_SIZE_WEIGHT=0.20
CLASSIFIER_PERFORATION_WEIGHT=0.15
# CLASSIFIER_MODEL_PATH=models/stamp_classifier.onnx  # Optional trained model

# Stage 1C: YOLO Fallback
DETECTION_FALLBACK_TO_YOLO=true
YOLO_MODEL_PATH=models/yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.5
YOLO_AUTO_DOWNLOAD=true

# =============================================================================
# Camera Settings
# =============================================================================
CAMERA_INDEX=0

# =============================================================================
# Feedback & Visualization Settings
# =============================================================================

# Session storage
SESSIONS_DIR=data/sessions
MISSED_STAMPS_DIR=data/missed_stamps

# Visualization
FEEDBACK_SAVE_ANNOTATED=true
FEEDBACK_SAVE_CROPS=true
FEEDBACK_SAVE_ORIGINAL=true
FEEDBACK_OPEN_ANNOTATED=false

# Overlay colors (BGR format)
OVERLAY_COLOR_IDENTIFIED=0,255,0
OVERLAY_COLOR_NO_MATCH=0,165,255
OVERLAY_COLOR_REJECTED=0,0,255
OVERLAY_COLOR_PENDING=0,255,255
OVERLAY_THICKNESS=2

# =============================================================================
# Browser Automation (CDP)
# =============================================================================
CHROME_CDP_URL=http://localhost:9222

# =============================================================================
# Default Themes for Colnect Scraping
# =============================================================================
DEFAULT_THEMES=Space,Space Traveling,Astronomy,Rockets,Satellites,Scientists

# =============================================================================
# Logging Settings
# =============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]
LOG_DIR=data/logs
LOG_MAX_SIZE_MB=2
LOG_BACKUP_COUNT=5

# =============================================================================
# Output Settings
# =============================================================================
OUTPUT_DIR=data

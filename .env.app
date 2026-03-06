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
# Vision LLM Detection (NEW - replaces OpenCV)
# =============================================================================

# Provider configuration groq
DETECTION_PRIMARY_PROVIDER=claude_haiku
DETECTION_FALLBACK_PROVIDER=groq
DETECTION_ENABLE_FALLBACK=true

# Groq settings
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
OLD_GROQ_MODEL=llama-3.2-11b-vision-preview
GROQ_RATE_LIMIT_PER_MINUTE=30

# Claude settings (fallback)
CLAUDE_HAIKU_MODEL=claude-3-haiku-20240307
CLAUDE_SONNET_MODEL=claude-3-5-sonnet-20241022

# Fallback triggers
DETECTION_MIN_DETECTIONS=1
DETECTION_FALLBACK_ON_PARSE_ERROR=true
DETECTION_FALLBACK_ON_API_ERROR=true

# =============================================================================
# Preprocessing Settings
# =============================================================================

# Strategy: original | downscale | compress | posterize | high_contrast | edge_enhanced | minimal
PREPROCESSING_STRATEGY=compress

# Resolution
PREPROCESSING_MAX_DIM=640

# JPEG compression (0-100, lower = smaller file)
PREPROCESSING_JPEG_QUALITY=85

# Posterization (colors per channel, 2-256)
PREPROCESSING_COLOR_LEVELS=8

# =============================================================================
# Identification Pipeline
# =============================================================================

# Mode: single | multi | auto
IDENTIFICATION_DEFAULT_MODE=auto

# Auto-detection of single stamp (in AUTO mode)
AUTO_DETECT_SINGLE_STAMP=true

# Crop padding (percentage)
CROP_PADDING_PERCENT=0.02

# =============================================================================
# Inspection & Debug
# =============================================================================

# Save all intermediate images and data
SAVE_INTERMEDIATES=true
DETECTION_SAVE_INTERMEDIATES=true

# Inspection output directory
INSPECTION_DIR=data/inspection
DETECTION_INSPECTION_DIR=data/inspection

# =============================================================================
# Session & Feedback Storage
# =============================================================================
SESSIONS_DIR=data/sessions
MISSED_STAMPS_DIR=data/missed_stamps

# Visualization
FEEDBACK_SAVE_ANNOTATED=true
FEEDBACK_SAVE_CROPS=true
FEEDBACK_SAVE_ORIGINAL=true
FEEDBACK_OPEN_ANNOTATED=false

# =============================================================================
# Vision Prompt
# =============================================================================
VISION_PROMPT_PATH=config/llava_prompt.txt

# =============================================================================
# Camera Settings
# =============================================================================
CAMERA_INDEX=0

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

# =============================================================================
# Roboflow Stamp Detector (local YOLOv8 model)
# =============================================================================

# Your workspace and project slugs from https://app.roboflow.com
ROBOFLOW_WORKSPACE=stamp-detector-wyo9i/1
ROBOFLOW_PROJECT=stamp-detector
ROBOFLOW_VERSION=1

# Local path where the downloaded .pt file is cached (auto-downloaded on first run)
ROBOFLOW_MODEL_PATH=models/roboflow_stamp_detector.pt

# Detection confidence threshold (lower = more detections, more false positives)
ROBOFLOW_CONFIDENCE_THRESHOLD=0.35

# Set to 'roboflow' to use local model as primary detector
# DETECTION_PRIMARY_PROVIDER=roboflow_local
# Options: roboflow | groq | claude_haiku | claude_sonnet
DETECTION_PRIMARY_PROVIDER=roboflow
DETECTION_FALLBACK_PROVIDER=claude_haiku
DETECTION_CLAUDE_MODEL_SONNET=claude-sonnet-4-20250514

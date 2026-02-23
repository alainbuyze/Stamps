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
# Object Detection (YOLO)
# =============================================================================
YOLO_MODEL_PATH=models/yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.5
YOLO_AUTO_DOWNLOAD=true

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

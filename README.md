# CoderDojo Guide Generator

Create printable Dutch instruction guides from online maker kit tutorials.

This tool automatically downloads tutorials from supported websites, translates them to Dutch, enhances images for print quality, and generates ready-to-print Markdown guides with QR codes and PDF output.

## Features

- **Web Scraping**: Fetches tutorial pages using Playwright (handles JavaScript-rendered content)
- **Content Extraction**: Extracts structured content (title, sections, images) using BeautifulSoup
- **MakeCode Replacement**: Automatically replaces English MakeCode screenshots with Dutch versions
- **Image Downloading**: Downloads all images locally for offline printing
- **Image Enhancement**: Optional 4x upscaling using Upscayl for better print quality
- **Dutch Translation**: Automatic translation using Google Translate (via deep-translator)
- **QR Code Generation**: Creates QR codes for hyperlinks in the guides
- **Markdown Output**: Generates clean Markdown files ready for printing
- **PDF Generation**: Converts guides to printable PDFs with optimized layouts
- **Catalog Generation**: Creates a catalog document summarizing all project guides
- **Batch Processing**: Process multiple tutorials with resume capability

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Upscayl](https://github.com/upscayl/upscayl) (optional, for image enhancement)
- GTK3 runtime (required for PDF generation with WeasyPrint on Windows)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Coderdojo
```

### 2. Install dependencies

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

### 3. Install Playwright browser

```bash
uv run playwright install chromium
# or: playwright install chromium
```

### 4. (Optional) Install Upscayl for image enhancement

Download and install from: https://github.com/upscayl/upscayl/releases

The tool will automatically detect Upscayl if installed in the default location:
- Windows: `C:\Program Files\Upscayl\`

## Commands

| Command | Description |
|---------|-------------|
| `generate` | Generate a guide from a single tutorial URL |
| `batch` | Generate guides from all tutorials on an index page |
| `catalog` | Generate a catalog document from all project guides |
| `print` | Convert a markdown guide to printable PDF |
| `print-all` | Convert all markdown files in a directory to PDFs |
| `sources` | List supported source websites |

## Usage

### Generate a single guide

```bash
uv run python -m src.cli generate --url "<TUTORIAL_URL>"
```

### Batch process all tutorials from an index page

```bash
uv run python -m src.cli batch --index "<INDEX_URL>"
```

### Generate a catalog from existing guides

```bash
uv run python -m src.cli catalog --input ./output
```

### Convert guides to PDF

```bash
uv run python -m src.cli print --input ./output/guide.md
uv run python -m src.cli print-all --input ./output
```

### List supported sources

```bash
uv run python -m src.cli sources
```

Currently supported:
- **wiki.elecfreaks.com** - Elecfreaks Wiki (Nezha Inventor's Kit tutorials)

## Command Options

| Option | Short | Description | Default | Commands |
|--------|-------|-------------|---------|----------|
| `--url` | | Tutorial page URL (required) | - | generate |
| `--index` | | Index page URL with tutorial links (required) | - | batch |
| `--input` | `-i` | Input file or directory (required) | - | print, print-all, catalog |
| `--output` | `-o` | Output directory or file path | OUTPUT_ROOT_DIR config | all except sources |
| `--title` | `-t` | Title for catalog document | "Project Catalogus" | catalog |
| `--css` | | Custom CSS file for PDF styling | resources/print.css | print, print-all |
| `--verbose` | `-v` | Enable verbose/debug output | False | all except sources |
| `--list-only` | | List tutorials without processing | False | batch |
| `--resume` | | Resume from previous batch state | False | batch |
| `--no-enhance` | | Skip Upscayl image enhancement | False | generate, batch |
| `--no-translate` | | Skip Dutch translation | False | generate, batch |
| `--no-qrcode` | | Skip QR code generation | False | generate, batch |
| `--no-makecode` | | Skip MakeCode screenshot replacement | False | generate, batch |
| `--no-download` | | Use existing images (skip download) | False | generate, batch |

## Output Structure

**Single tutorial (generate):**
```
output/
├── Project 01 - Title.md          # Dutch Markdown guide
└── Project 01 - Title/
    ├── images/                    # Downloaded and enhanced images
    └── qrcodes/                   # QR codes for hyperlinks
```

**Batch processing (batch):**
```
output/
├── Project 01 - Title.md
├── Project 01 - Title/images/
├── Project 02 - Title.md
├── Project 02 - Title/images/
└── .batch_state.json              # Resume state (auto-cleaned on success)
```

**Catalog (catalog):**
```
output/
└── catalog.md                     # Catalog with TOC and project summaries
```

## Configuration

Configuration is managed via environment variables or `.env.app` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT_ROOT_DIR` | `./output` | Default output directory |
| `CACHE_DIR` | `./cache` | Cache for downloaded pages |
| `RATE_LIMIT_SECONDS` | `2` | Delay between batch requests |
| `IMAGE_DOWNLOAD_TIMEOUT` | `30` | Image download timeout (seconds) |
| `UPSCAYL_PATH` | Auto-detected | Path to Upscayl binary |
| `UPSCAYL_SCALE` | `4` | Upscale factor (2 or 4) |
| `UPSCAYL_MODEL` | `realesrgan-x4plus` | Upscayl model to use |
| `MAKECODE_REPLACE_ENABLED` | `true` | Enable MakeCode screenshot replacement |
| `MAKECODE_LANGUAGE` | `nl` | Target language for MakeCode |
| `MAKECODE_TIMEOUT` | `30000` | MakeCode capture timeout (ms) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Project Structure

```
src/
├── cli.py                  # Command-line interface
├── scraper.py              # Playwright-based page fetcher
├── extractor.py            # Content extraction orchestrator
├── downloader.py           # Async image downloader
├── enhancer.py             # Upscayl image enhancement
├── translator.py           # Dutch translation
├── generator.py            # Markdown generation
├── printer.py              # PDF generation with WeasyPrint
├── catalog.py              # Catalog generation from guides
├── makecode_detector.py    # Detects MakeCode links and code images
├── makecode_capture.py     # Captures Dutch MakeCode screenshots
├── makecode_replacer.py    # Replaces English screenshots with Dutch
├── qrcode_generator.py     # QR code generation for hyperlinks
├── core/
│   ├── config.py           # Settings management
│   ├── errors.py           # Custom exceptions
│   └── logging.py          # Logging setup
└── sources/
    ├── base.py             # Base source adapter
    └── elecfreaks.py       # Elecfreaks-specific extraction
```

## Development

### Run tests

```bash
uv run pytest
```

### Run linting

```bash
uv run ruff check src/
uv run ruff format src/
```

### Install dev dependencies

```bash
uv sync --all-extras
```

## Pipeline Flow

```
URL → Fetch → Extract → MakeCode → Download → Enhance → Translate → Generate → QR Codes → Save
      (Playwright) (BS4)  (Playwright) (httpx)  (Upscayl)  (Google)   (Markdown)  (qrcode)
```

**Pipeline Stages:**
1. **Fetch**: Download HTML content from the tutorial URL
2. **Extract**: Parse and extract structured content (title, sections, images)
3. **MakeCode**: Replace MakeCode screenshots with Dutch versions (if enabled)
4. **Download**: Fetch all images and store locally (or use existing if `--no-download`)
5. **Enhance**: AI-enhance images for better quality (if enabled)
6. **Translate**: Convert content to Dutch (if enabled)
7. **Generate**: Create markdown guide with local image references
8. **QR Codes**: Generate QR codes for hyperlinks (if enabled)
9. **Save**: Write guide to filesystem

Each stage handles errors gracefully:
- **Critical failures** (fetch, extract, generate, save): Stop with error message
- **Non-critical failures** (download, enhance, translate, makecode, qrcode): Log warning, continue with fallback

## Troubleshooting

### "No adapter available for URL"

The URL is not from a supported source. Run `sources` command to see supported websites.

### Image enhancement fails

- Ensure Upscayl is installed
- Check that `UPSCAYL_PATH` points to the correct binary
- Use `--no-enhance` to skip enhancement

### Translation fails

- Check internet connection (requires Google Translate API)
- Use `--no-translate` to skip translation and keep English

### MakeCode replacement fails

- Ensure you have a working internet connection
- MakeCode editor must be accessible
- Use `--no-makecode` to skip replacement and keep original images

### PDF generation fails (Windows)

- Install GTK3 runtime for WeasyPrint: https://github.com/nicotine-plus/nicotine-plus/issues/1826
- Ensure all required fonts are installed
- Check that the markdown file and images exist

### Browser errors

```bash
# Reinstall Playwright browsers
uv run playwright install chromium
```

### Resume batch processing

If batch processing is interrupted, use `--resume` to continue:
```bash
uv run python -m src.cli batch --index "<URL>" --resume
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `uv run pytest`
4. Run linting: `uv run ruff check src/`
5. Submit a pull request

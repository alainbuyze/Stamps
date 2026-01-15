# CoderDojo Guide Generator - Product Requirements Document

## 1. Executive Summary

The CoderDojo Guide Generator is a Python-based tool designed to help CoderDojo volunteers create printable, Dutch-language instruction guides from online educational resources. Many maker kits (like the Elecfreaks Nezha Inventor's Kit) provide instructions only in English and only online, making them difficult for Dutch-speaking children to follow during hands-on sessions.

This tool automates the process of downloading web-based tutorials, extracting relevant content, enhancing low-quality images, translating text to Dutch, and generating clean, printable Markdown documents. It supports both single-guide generation and batch processing of entire kit collections.

**MVP Goal:** Create a working pipeline that can process Elecfreaks wiki pages into high-quality Dutch Markdown guides with enhanced images, ready for printing.

## 2. Mission

**Mission Statement:** Empower CoderDojo volunteers to easily create accessible, high-quality printed instruction materials in Dutch for children's maker projects.

**Core Principles:**
1. **Accessibility First** - Remove barriers by providing Dutch instructions in printable format
2. **Quality Enhancement** - Improve source material quality (especially images) rather than just copying
3. **Batch Efficiency** - Process entire kit collections with minimal manual intervention
4. **Maintainability** - Clean, modular code that volunteers can extend for new kit sources
5. **Offline-Ready** - Generated guides work completely offline once printed

## 3. Target Users

**Primary User: CoderDojo Volunteer/Mentor**
- Technical comfort: Comfortable running Python scripts from command line
- Needs: Quick way to prepare printed materials for sessions
- Pain points: Manually translating and formatting guides is time-consuming; online-only instructions don't work well in classroom settings

**Secondary User: CoderDojo Organizer**
- Technical comfort: Basic computer skills
- Needs: Library of pre-generated guides for multiple kits
- Pain points: Inconsistent quality of available materials; language barrier for Dutch children

## 4. MVP Scope

### In Scope

**Core Functionality:**
- ✅ Download single tutorial page from URL
- ✅ Download all tutorials from an index page (batch mode)
- ✅ Extract main content, removing navigation/sidebars/footers
- ✅ Download all images from tutorial
- ✅ Enhance images using Upscayl
- ✅ Translate text content to Dutch
- ✅ Generate clean Markdown output
- ✅ Organize output in structured folders

**Technical:**
- ✅ Playwright for page rendering (handles JavaScript)
- ✅ BeautifulSoup for HTML parsing
- ✅ Upscayl integration for image enhancement
- ✅ Command-line interface
- ✅ Progress reporting during batch operations
- ✅ Resume capability for interrupted batch jobs

**Supported Sources:**
- ✅ Elecfreaks Wiki (wiki.elecfreaks.com)

### Out of Scope

- ❌ GUI interface
- ❌ PDF generation (use Markdown viewer/printer instead)
- ❌ Real-time translation API (use local/free translation)
- ❌ Support for other kit manufacturers (future phase)
- ❌ Automatic printing
- ❌ Cloud deployment
- ❌ Multi-language support beyond Dutch

## 5. User Stories

1. **As a CoderDojo volunteer**, I want to generate a Dutch guide from a single tutorial URL, so that I can quickly prepare materials for a specific project session.
   - *Example:* `python guide_gen.py --url "https://wiki.elecfreaks.com/.../case_01" --output ./guides`

2. **As a CoderDojo volunteer**, I want to batch-process all tutorials from a kit index page, so that I can prepare a complete set of materials at once.
   - *Example:* `python guide_gen.py --index "https://wiki.elecfreaks.com/.../nezha-inventors-kit/" --output ./guides`

3. **As a CoderDojo volunteer**, I want images to be automatically enhanced, so that printed guides have clear, readable diagrams without manual editing.
   - *Example:* Low-resolution assembly images are upscaled to 2x/4x resolution

4. **As a CoderDojo volunteer**, I want to resume an interrupted batch job, so that I don't have to restart from scratch if something fails.
   - *Example:* `python guide_gen.py --resume --output ./guides`

5. **As a CoderDojo organizer**, I want guides organized in a consistent folder structure, so that I can easily find and distribute materials.
   - *Example:* Output organized as `guides/nezha-kit/case_01_mechanical_shrimp/guide.md`

6. **As a CoderDojo volunteer**, I want a preview of detected tutorials before batch processing, so that I can verify the correct pages will be processed.
   - *Example:* `python guide_gen.py --index "..." --list-only`

## 6. Core Architecture & Patterns

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                             │
│                    (guide_gen.py / click)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Pipeline Orchestrator                       │
│                   (coordinates all stages)                       │
└─────────────────────────────────────────────────────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│  Scraper  │  │ Extractor │  │  Enhancer │  │ Generator │
│(Playwright)│  │(Beautiful │  │ (Upscayl) │  │(Markdown) │
│           │  │   Soup)   │  │           │  │           │
└───────────┘  └───────────┘  └───────────┘  └───────────┘
                                    │
                                    ▼
                            ┌───────────┐
                            │Translator │
                            │ (Dutch)   │
                            └───────────┘
```

### Directory Structure

```
coderdojo/
├── src/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── pipeline.py         # Orchestrates the full workflow
│   ├── scraper.py          # Playwright-based page fetcher
│   ├── extractor.py        # BeautifulSoup content extraction
│   ├── enhancer.py         # Upscayl image processing
│   ├── translator.py       # Dutch translation
│   ├── generator.py        # Markdown generation
│   └── sources/
│       ├── __init__.py
│       ├── base.py         # Base source adapter
│       └── elecfreaks.py   # Elecfreaks-specific extraction rules
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   ├── test_extractor.py
│   ├── test_enhancer.py
│   └── fixtures/           # Sample HTML for testing
├── output/                 # Generated guides (gitignored)
├── cache/                  # Downloaded pages cache (gitignored)
├── pyproject.toml
├── CLAUDE.md
└── PRD.md
```

### Key Design Patterns

1. **Pipeline Pattern** - Each stage (scrape → extract → enhance → translate → generate) is independent and composable
2. **Adapter Pattern** - Source-specific extraction rules (`sources/elecfreaks.py`) implement a common interface
3. **Strategy Pattern** - Translation and enhancement can swap implementations
4. **Repository Pattern** - Cache manager handles downloaded content persistence

## 7. Tools/Features

### 7.1 Page Scraper (Playwright)

**Purpose:** Download fully-rendered web pages including JavaScript content

**Operations:**
- `fetch_page(url)` - Download and render a single page
- `fetch_index(url)` - Extract all tutorial links from index page
- `download_images(page, output_dir)` - Download all images from page

**Key Features:**
- Headless browser operation
- Automatic wait for content rendering
- Image URL extraction and download
- Rate limiting to avoid blocking

### 7.2 Content Extractor (BeautifulSoup)

**Purpose:** Extract relevant tutorial content, removing navigation clutter

**Operations:**
- `extract_content(html)` - Get main article content
- `extract_metadata(html)` - Get title, description
- `extract_images(html)` - Get image references with context
- `clean_html(element)` - Remove unwanted attributes/elements

**Elecfreaks-Specific Rules:**
- Main content: `article` or `.markdown` container
- Remove: `.sidebar`, `.navbar`, `.footer`, `.breadcrumb`, `.toc`
- Images: All `img` tags within main content
- Code blocks: Preserve MakeCode/Python snippets

### 7.3 Image Enhancer (Upscayl)

**Purpose:** Upscale low-quality images for better print quality

**Operations:**
- `enhance_image(input_path, output_path)` - Upscale single image
- `enhance_batch(input_dir, output_dir)` - Process all images in folder

**Configuration:**
- Upscayl path: `C:\Program Files\Upscayl\Upscayl.exe`
- Scale factor: 2x (configurable)
- Model: Real-ESRGAN (default)
- Skip if image already high-resolution (>1000px)

### 7.4 Translator

**Purpose:** Translate English content to Dutch

**Operations:**
- `translate_text(text, source='en', target='nl')` - Translate string
- `translate_markdown(md_content)` - Translate preserving formatting

**Implementation Options (in order of preference):**
1. **Deep Translator** (free, uses Google Translate API)
2. **Argos Translate** (offline, open source)
3. **Manual glossary** for technical terms

### 7.5 Markdown Generator

**Purpose:** Generate clean, printable Markdown output

**Operations:**
- `generate_guide(content, images, metadata)` - Create full guide
- `format_steps(steps)` - Format assembly/coding steps
- `embed_images(images, style)` - Reference images with captions

**Output Format:**
```markdown
# [Project Title in Dutch]

## Materialen
[Components list with images]

## Montage
[Step-by-step assembly with numbered images]

## Aansluitschema
[Connection diagram]

## Programmeren
[MakeCode/Python instructions]

## Resultaat
[Expected outcome with demo image/GIF]
```

## 8. Technology Stack

### Backend (Python 3.11+)

| Component | Package | Version | Purpose |
|-----------|---------|---------|---------|
| CLI | click | ^8.1 | Command-line interface |
| Browser automation | playwright | ^1.40 | Page rendering & scraping |
| HTML parsing | beautifulsoup4 | ^4.12 | Content extraction |
| HTTP client | httpx | ^0.26 | Image downloads |
| Translation | deep-translator | ^1.11 | English to Dutch |
| Markdown | markdownify | ^0.11 | HTML to Markdown conversion |
| Progress | rich | ^13.7 | Progress bars & formatting |
| Config | pydantic | ^2.5 | Settings validation |

### External Tools

| Tool | Path | Purpose |
|------|------|---------|
| Upscayl | `C:\Program Files\Upscayl\Upscayl.exe` | Image enhancement |

### Development Tools

| Tool | Purpose |
|------|---------|
| uv | Package management |
| pytest | Testing |
| ruff | Linting & formatting |

## 9. Security & Configuration

### Configuration (Environment Variables)

```bash
# .env.example
UPSCAYL_PATH="C:\Program Files\Upscayl\Upscayl.exe"
OUTPUT_DIR="./output"
CACHE_DIR="./cache"
IMAGE_SCALE_FACTOR=2
RATE_LIMIT_SECONDS=2
```

### Configuration (config.toml alternative)

```toml
[paths]
upscayl = "C:\\Program Files\\Upscayl\\Upscayl.exe"
output = "./output"
cache = "./cache"

[scraping]
rate_limit_seconds = 2
timeout_seconds = 30
headless = true

[enhancement]
scale_factor = 2
min_size_to_skip = 1000
model = "realesrgan-x4plus"

[translation]
source_language = "en"
target_language = "nl"
```

### Security Scope

**In Scope:**
- ✅ Respect rate limits to avoid IP blocking
- ✅ Cache downloaded content to minimize requests
- ✅ Validate URLs before processing

**Out of Scope:**
- ❌ Authentication (target sites are public)
- ❌ User data handling
- ❌ Network security beyond HTTPS

## 10. CLI Specification

### Commands

```bash
# Single guide generation
python -m coderdojo.cli generate --url <URL> [--output <DIR>] [--no-enhance] [--no-translate]

# Batch generation from index
python -m coderdojo.cli batch --index <URL> [--output <DIR>] [--list-only] [--resume]

# List supported sources
python -m coderdojo.cli sources

# Clear cache
python -m coderdojo.cli cache clear
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--url` | Single tutorial URL | Required for `generate` |
| `--index` | Index page URL with multiple tutorials | Required for `batch` |
| `--output`, `-o` | Output directory | `./output` |
| `--no-enhance` | Skip image enhancement | False |
| `--no-translate` | Keep English (skip translation) | False |
| `--list-only` | Show detected tutorials without processing | False |
| `--resume` | Continue interrupted batch job | False |
| `--verbose`, `-v` | Verbose output | False |

### Example Usage

```bash
# Generate single guide
python -m coderdojo.cli generate \
  --url "https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/Nezha_Inventor_s_kit_for_microbit_case_01" \
  --output ./guides

# Generate all 76 Nezha kit guides
python -m coderdojo.cli batch \
  --index "https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/" \
  --output ./guides

# Preview what would be processed
python -m coderdojo.cli batch \
  --index "https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/" \
  --list-only
```

## 11. Success Criteria

### MVP Success Definition

The MVP is successful when a CoderDojo volunteer can:
1. Run a single command to generate a Dutch guide from an Elecfreaks URL
2. Get a printable Markdown file with enhanced images
3. Process an entire kit (76 guides) overnight with resume capability

### Functional Requirements

- ✅ Successfully scrape Elecfreaks wiki pages
- ✅ Extract main content without navigation clutter
- ✅ Download all images from tutorials
- ✅ Enhance images using Upscayl (2x minimum)
- ✅ Translate all text to Dutch
- ✅ Generate valid Markdown output
- ✅ Batch process with progress indication
- ✅ Resume interrupted batch jobs

### Quality Indicators

- Image enhancement completes without errors for >95% of images
- Translation preserves technical terms correctly
- Generated Markdown renders correctly in standard viewers
- Batch processing handles rate limits without IP blocking

### User Experience Goals

- Clear progress indication during long batch operations
- Helpful error messages when something fails
- Generated guides are immediately printable

## 12. Implementation Phases

### Phase 1: Foundation

**Goal:** Basic scraping and content extraction working

**Deliverables:**
- ✅ Project structure and dependencies
- ✅ Playwright-based page scraper
- ✅ BeautifulSoup content extractor for Elecfreaks
- ✅ Basic CLI with `generate` command
- ✅ Raw Markdown output (no enhancement/translation)

**Validation:**
- Can download and extract content from Case 01
- Output contains all text and image references
- No navigation/sidebar content in output

### Phase 2: Enhancement Pipeline

**Goal:** Image enhancement and translation working

**Deliverables:**
- ✅ Upscayl integration for image enhancement
- ✅ Image download and organization
- ✅ Dutch translation integration
- ✅ Enhanced Markdown output with embedded images

**Validation:**
- Images are visibly improved in quality
- Dutch translation is readable and accurate
- Guide is print-ready

### Phase 3: Batch Processing

**Goal:** Process entire kit collections efficiently

**Deliverables:**
- ✅ Index page parsing for tutorial links
- ✅ Batch command with progress reporting
- ✅ Resume capability for interrupted jobs
- ✅ Rate limiting and caching

**Validation:**
- Can process all 76 Nezha kit guides
- Resume works after interruption
- No IP blocking during batch operations

### Phase 4: Polish & Documentation

**Goal:** Production-ready tool with documentation

**Deliverables:**
- ✅ Error handling and edge cases
- ✅ User documentation (README)
- ✅ Sample output guides
- ✅ Technical term glossary for translation

**Validation:**
- Tool runs reliably for all supported pages
- Documentation sufficient for other volunteers
- Generated guides used successfully in CoderDojo session

## 13. Future Considerations

### Post-MVP Enhancements

- **Additional Sources:** Support for other kit manufacturers (Keyestudio, DFRobot, etc.)
- **PDF Export:** Direct PDF generation with proper styling
- **GUI Interface:** Simple web-based UI for non-technical users
- **Multiple Languages:** Support for French, German, etc.
- **Custom Templates:** Allow customizing output format/styling

### Integration Opportunities

- **GitHub Actions:** Automated guide generation when source pages update
- **CoderDojo Portal:** Integration with CoderDojo resource sharing platform
- **Print Services:** Direct integration with print-on-demand services

### Advanced Features

- **OCR Enhancement:** Extract text from diagram images
- **Video Tutorials:** Extract frames from linked videos
- **Diff Detection:** Alert when source pages change

## 14. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Website structure changes** | High - breaks extraction | Medium | Modular source adapters; test suite with fixtures |
| **IP blocking during batch** | Medium - interrupts processing | Medium | Rate limiting; caching; resume capability |
| **Upscayl CLI limitations** | Medium - manual workaround needed | Low | Research CLI options; fallback to GUI automation |
| **Translation quality** | Medium - confusing instructions | Medium | Technical term glossary; manual review option |
| **Large batch processing time** | Low - inconvenience | High | Progress reporting; background/overnight runs |

## 15. Appendix

### Related Resources

- [Elecfreaks Nezha Kit Wiki](https://wiki.elecfreaks.com/en/microbit/building-blocks/nezha-inventors-kit/)
- [Upscayl GitHub](https://github.com/upscayl/upscayl)
- [Upscayl-NCNN CLI](https://github.com/upscayl/upscayl-ncnn)
- [Playwright Python Docs](https://playwright.dev/python/)
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Sample Page Analysis: Case 01 (Mechanical Shrimp)

**Content Structure:**
- 1 Introduction section
- 1 Materials/components list
- 33 Assembly step images
- 1 Connection diagram
- 6 MakeCode programming screenshots
- 1 Result GIF

**Image Hosting:**
- CDN: `wiki-media-ef.oss-cn-hongkong.aliyuncs.com`
- Format: PNG (photos), GIF (animations)

### Technical Terms Glossary (EN → NL)

| English | Dutch |
|---------|-------|
| micro:bit | micro:bit |
| servo | servomotor |
| motor | motor |
| sensor | sensor |
| LED | LED |
| connection diagram | aansluitschema |
| assembly | montage |
| components | onderdelen |
| step | stap |
| result | resultaat |

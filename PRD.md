# Stamp Collection Toolset — Product Requirements Document

**Version:** 1.0
**Date:** 2026-02-22
**Author:** Generated via PRD Discovery Process

---

## 1. Executive Summary

The Stamp Collection Toolset is a Python-based CLI application designed to help a philatelist manage a 6,000+ stamp collection focused on space exploration themes. The toolset addresses three core challenges: building a searchable AI-enhanced database of space-themed stamps from Colnect, identifying physical stamps via camera using computer vision and semantic search, and migrating an existing collection from LASTDODO to Colnect.

The solution leverages modern AI capabilities (Groq vision API for image descriptions, OpenAI for embeddings, YOLOv8 for object detection) combined with a vector database (Supabase) for similarity search. Browser automation via Playwright enables seamless integration with Colnect for collection management without requiring an API.

This is a single-user tool built for a technically proficient user comfortable with Python and CLI interfaces. The architecture prioritizes low cost (targeting free/minimal tiers), simplicity (Colnect as the source of truth), and practicality (one-time setup with occasional re-runs).

---

## 2. Glossary

| Term | Definition |
|------|------------|
| **Colnect** | Online stamp catalog and collector community — primary collection management system |
| **LASTDODO** | Dutch collectibles marketplace — source for one-time collection import |
| **RAG** | Retrieval-Augmented Generation — local index for stamp identification via similarity search |
| **MNH** | Mint Never Hinged — stamp with original gum, never mounted |
| **Used** | Stamp that has been postally used (cancelled) |
| **CTO** | Cancelled To Order — stamp cancelled without postal use (often for collectors) |
| **CDP** | Chrome DevTools Protocol — allows programmatic control of a running Chrome browser |
| **YOLOv8** | Latest YOLO object detection model by Ultralytics |
| **Groq** | AI inference platform optimized for speed, offers vision models |
| **Label Studio** | Open-source data labeling tool for ML training datasets |
| **pgvector** | PostgreSQL extension for vector similarity search |

---

## 3. Mission

**Mission Statement:** Enable rapid identification of physical stamps through AI-powered image recognition and maintain a consolidated digital collection in Colnect.

**Core Principles:**
- **Simplicity over features** — Colnect remains the source of truth; the toolset is a companion, not a replacement
- **Low cost** — Leverage free tiers and minimal API usage; total ongoing cost < €1/month
- **Practical automation** — Automate repetitive tasks while keeping the user in control of decisions
- **Resilience** — Long-running operations support checkpoint/resume; errors don't cause data loss

---

## 4. Target Users

**Primary Persona:** Technical stamp collector (single user)

- **Technical Level:** High — comfortable with Python, CLI, configuration files, AI concepts
- **Key Needs:**
  - Quickly identify unknown stamps by pointing a camera
  - Have a comprehensive searchable index of space-themed stamps
  - Migrate existing LASTDODO collection to Colnect
- **Pain Points:**
  - Manual catalog lookup is time-consuming
  - Collection split across platforms (LASTDODO, Colnect)
  - No unified search across physical and digital inventory

---

## 5. MVP Scope (MoSCoW)

### Must Have (MVP Critical)

| ID | Feature |
|----|---------|
| M1 | Colnect scraper for space themes |
| M2 | Groq vision API integration for stamp descriptions |
| M3 | OpenAI embeddings for semantic search |
| M4 | Supabase RAG index (insert/search) |
| M5 | CLI camera capture |
| M6 | YOLO stamp detection (pre-trained model) |
| M7 | RAG-based identification with threshold (>90% auto, else top 3) |
| M8 | LASTDODO collection scraper |
| M9 | Catalog number matching (Michel, Yvert, Scott, SG, Fisher) |
| M10 | Condition mapping (Postfris→MNH, Gestempeld→Used) |
| M11 | Browser automation for Colnect (add to collection) |
| M12 | Dry-run mode for import |
| M13 | Configuration file support (.env) |
| M14 | Detailed logging throughout |
| M15 | CLI-based manual review for unmatched stamps |

### Should Have (High Priority)

| ID | Feature |
|----|---------|
| S1 | Checkpoint/resume for long scrapes |
| S2 | Partial re-ingestion by country/year |
| S3 | Description regeneration capability |
| S4 | Multi-stamp batch processing in camera mode |
| S5 | Configurable error handling behavior |
| S6 | Rate limiting configuration |
| S7 | Import summary report |

### Could Have (If Time Permits)

| ID | Feature |
|----|---------|
| C1 | Web UI for manual review queue |
| C2 | YOLO training pipeline with Label Studio |
| C3 | Colnect "already owned" detection |
| C4 | Progress bar / ETA for long operations |
| C5 | Multiple LLaVA prompt templates |
| C6 | Statistics dashboard |

### Won't Have (This Version)

| ID | Feature |
|----|---------|
| W1 | Bidirectional LASTDODO sync |
| W2 | Local full catalog database |
| W3 | Mobile app / tablet interface |
| W4 | Multi-user support |
| W5 | Stamp valuation / pricing features |
| W6 | Social features / sharing |
| W7 | OCR for text extraction (Groq vision handles) |

---

## 6. User Stories

### Use Case 1: Initialization (RAG Database Building)

#### Story 1.1: Scrape Colnect Space-Themed Stamps

**As a** collector, **I want to** scrape stamp data from Colnect for configurable themes (Space, Astronomy, Scientists, etc.), **so that** I have a comprehensive source dataset for identification.

**Acceptance Criteria:**
- [ ] Given a list of theme keywords, when scraping is initiated, then all stamps matching those themes are discovered
- [ ] Given rate limiting is set to "polite", when scraping runs, then requests are spaced 1-2 seconds apart
- [ ] Given a stamp page is loaded, then the following data is extracted: Colnect ID, title, country, year, image URL, themes, catalog codes, and page URL
- [ ] Given scraping encounters an error, when configured to "skip and log", then the stamp is logged for retry and scraping continues
- [ ] Given scraping is interrupted, when resumed, then it continues from where it left off (checkpoint support)

#### Story 1.2: Generate Stamp Descriptions

**As a** collector, **I want to** generate AI descriptions for each stamp image using Groq vision API, **so that** I have rich text for semantic search in the RAG.

**Acceptance Criteria:**
- [ ] Given a stamp image URL, when Groq processes it, then a description is generated including: visual elements, country name, denomination, year (if visible), colors, and depicted subject
- [ ] Given Groq processing fails, then the stamp is flagged and processing continues
- [ ] Given a stamp already has a description, when regeneration is requested, then the old description is replaced
- [ ] Given the prompt template is modified in `config/llava_prompt.txt`, then subsequent descriptions use the new prompt

#### Story 1.3: Build RAG Index in Supabase

**As a** collector, **I want to** store stamp descriptions with vector embeddings in Supabase, **so that** I can perform similarity searches for identification.

**Acceptance Criteria:**
- [ ] Given a stamp with description, when indexed, then the following is stored: Colnect ID, description text, embedding vector, country, year, image URL, Colnect URL
- [ ] Given a stamp already exists in RAG, when re-indexed, then the existing entry is updated (upsert)
- [ ] Given embedding generation fails, then the error is logged and the stamp is flagged

#### Story 1.4: Partial Re-ingestion

**As a** collector, **I want to** re-scrape and re-index stamps filtered by country and/or year, **so that** I can update specific portions of the database without full re-processing.

**Acceptance Criteria:**
- [ ] Given filter `--country=Australia`, when re-ingestion runs, then only Australian stamps are processed
- [ ] Given filter `--year=2021`, when re-ingestion runs, then only stamps from 2021 are processed
- [ ] Given both filters, when combined, then they are applied with AND logic

---

### Use Case 2: Stamp Detection & Identification

#### Story 2.1: Capture Image via Camera

**As a** collector, **I want to** capture a single frame from my PC camera via CLI, **so that** I can identify stamps in the image.

**Acceptance Criteria:**
- [ ] Given the CLI command is executed, when a camera is available, then a single frame is captured
- [ ] Given multiple cameras are available, when no camera is specified, then the default camera is used (configurable)
- [ ] Given no camera is available, then a clear error message is shown
- [ ] Given capture succeeds, then the image is held in memory (not saved to disk)

#### Story 2.2: Detect Stamps in Image (YOLO)

**As a** collector, **I want to** automatically detect all stamp boundaries in a captured image, **so that** individual stamps can be extracted for identification.

**Acceptance Criteria:**
- [ ] Given an image with one or more stamps, when YOLO processes it, then bounding boxes are returned for each detected stamp
- [ ] Given an image with no stamps, then an empty result is returned with a message
- [ ] Given multiple stamps detected, then all are processed automatically

#### Story 2.3: Identify Stamp via RAG Search

**As a** collector, **I want to** match a detected stamp against the RAG database using its description, **so that** I know which catalog entry it corresponds to.

**Acceptance Criteria:**
- [ ] Given a cropped stamp image, when Groq generates a description, then a vector similarity search is performed against Supabase
- [ ] Given similarity score > 90%, then the match is auto-accepted and displayed
- [ ] Given similarity score ≤ 90%, then top 3 matches are displayed with scores for user selection
- [ ] Given no matches above minimum threshold (50%), then "no match found" is displayed with option to search manually

#### Story 2.4: Add Identified Stamp to Colnect Collection

**As a** collector, **I want to** automatically add a confirmed stamp to my Colnect collection via browser automation, **so that** I don't have to manually navigate and click.

**Acceptance Criteria:**
- [ ] Given a confirmed match with Colnect URL, when "add to collection" is triggered, then Playwright opens the page and performs the add action
- [ ] Given user is not logged into Colnect, then a prompt appears to log in first
- [ ] Given addition succeeds, then confirmation is displayed
- [ ] Given addition fails, then the error is displayed with the Colnect URL for manual action

---

### Use Case 3: LASTDODO Migration

#### Story 3.1: Scrape LASTDODO Collection

**As a** collector, **I want to** extract all stamps from my LASTDODO collection via web scraping, **so that** I have a dataset to import into Colnect.

**Acceptance Criteria:**
- [ ] Given logged-in LASTDODO session, when scraping runs, then all 6,143 items are extracted
- [ ] Given each item, then the following is captured: title, catalog numbers (Michel, Yvert, Scott, SG, Fisher), country, year, condition, quantity, image URL
- [ ] Given pagination exists, then all pages are processed
- [ ] Given scraping encounters rate limiting, then polite delays are applied


#### Story 3.2: Match LASTDODO Stamps to Colnect

**As a** collector, **I want to** match LASTDODO stamps to Colnect entries by catalog number, **so that** I can link my existing collection to the new platform.

**Acceptance Criteria:**
- [ ] Given a stamp with catalog number, when matched against Colnect, then the Colnect entry is identified
- [ ] Given matching priority: Michel → Yvert → Scott → SG → Fisher, when first match found, then it is used
- [ ] Given no catalog number match, then the stamp is flagged for manual review with image and metadata

#### Story 3.3: Map Conditions and Quantities

**As a** collector, **I want to** consolidate multiple condition variants of the same stamp into a single Colnect entry with breakdown in comments, **so that** my collection accurately reflects what I own.

**Acceptance Criteria:**
- [ ] Given stamps with Postfris or Ongebruikt condition, then Colnect condition is set to MNH
- [ ] Given stamps with Gestempeld condition, then Colnect condition is set to Used
- [ ] Given both MNH and Used variants exist for the same stamp, then MNH takes precedence for the condition field
- [ ] Given multiple variants, then comment field contains breakdown (e.g., `MNH:3, U:1`)
- [ ] Given multiple variants, then quantity field contains total count

#### Story 3.4: Import to Colnect via Browser Automation

**As a** collector, **I want to** add matched stamps to my Colnect collection via browser automation, **so that** the migration is automated.

**Acceptance Criteria:**
- [ ] Given matched stamp data, when import runs in live mode, then Playwright adds the stamp to Colnect with correct condition, quantity, and comment
- [ ] Given dry-run mode is enabled, then all steps are logged but no Colnect updates occur
- [ ] Given import of a stamp fails, then the error is logged and import continues with next stamp
- [ ] Given import completes, then a summary report shows: successful imports, failures, items pending manual review

#### Story 3.5: Manual Review Queue

**As a** collector, **I want to** manually review unmatched stamps and provide Colnect IDs, **so that** the migration is complete.

**Acceptance Criteria:**
- [ ] Given items flagged for review, when review command runs, then items are displayed one at a time with metadata
- [ ] Given user provides Colnect URL or ID, then the match is recorded and item can be imported
- [ ] Given user chooses to skip, then item is marked as skipped

---

## 7. Data Model

### Entities

#### CatalogStamp (Local SQLite)

Minimal stamp data scraped from Colnect for RAG ingestion.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| colnect_id | string | Yes | Unique Colnect identifier |
| colnect_url | string | Yes | Full URL to stamp page |
| title | string | Yes | Stamp title/name |
| country | string | Yes | Issuing country |
| year | integer | Yes | Year of issue |
| themes | JSON | No | Theme tags for filtering |
| image_url | string | Yes | Direct URL to stamp image on Colnect |
| catalog_codes | JSON | No | `{michel, scott, yvert, sg, fisher}` |
| scraped_at | datetime | Yes | When scraped |

#### RAGEntry (Supabase)

Searchable entry for stamp identification.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Supabase primary key |
| colnect_id | string | Yes | Unique Colnect identifier |
| colnect_url | string | Yes | Link to stamp page |
| image_url | string | Yes | Direct link to stamp image |
| description | text | Yes | Groq-generated description |
| embedding | vector(1536) | Yes | OpenAI text-embedding-3-small |
| country | string | Yes | Filter attribute |
| year | integer | Yes | Filter attribute |
| created_at | datetime | Yes | When indexed |
| updated_at | datetime | Yes | Last update |

#### LastdodoItem (Local SQLite)

Stamp from LASTDODO collection with catalog identifiers.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| lastdodo_id | string | Yes | Unique LASTDODO identifier |
| title | string | Yes | Item title |
| country | string | No | Country if extractable |
| year | integer | No | Year if extractable |
| michel_number | string | No | Michel catalog number |
| yvert_number | string | No | Yvert et Tellier number |
| scott_number | string | No | Scott catalog number |
| sg_number | string | No | Stanley Gibbons number |
| fisher_number | string | No | Fisher catalog number |
| condition | string | Yes | Dutch: Postfris, Gestempeld, Ongebruikt |
| condition_mapped | string | Yes | English: MNH, Used |
| quantity | integer | Yes | Number owned |
| value_eur | decimal | No | Catalog value |
| image_url | string | No | LASTDODO image URL |
| scraped_at | datetime | Yes | When scraped |

#### ImportTask (Local SQLite)

Tracks migration of LASTDODO item to Colnect.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| id | uuid | Yes | Task identifier |
| lastdodo_id | string | Yes | Source item |
| colnect_id | string | No | Matched Colnect stamp |
| status | enum | Yes | pending, matched, needs_review, imported, failed, skipped |
| match_method | string | No | Which catalog matched: michel, yvert, scott, sg, fisher, manual |
| condition_final | string | No | MNH or Used |
| quantity_final | integer | No | Total quantity |
| comment | string | No | Breakdown: `MNH:3, U:1` |
| error_message | string | No | Error if failed |
| reviewed_at | datetime | No | Manual review timestamp |
| imported_at | datetime | No | Import timestamp |
| dry_run | boolean | Yes | Dry run flag |

### Validation Rules

- `colnect_id` must be unique across CatalogStamp and RAGEntry
- `lastdodo_id` must be unique in LastdodoItem
- `condition_mapped` must be one of: MNH, Used
- `status` in ImportTask must be one of: pending, matched, needs_review, imported, failed, skipped
- `embedding` must be exactly 1536 dimensions

---

## 8. Technology Stack

| Component | Technology | Version | Cost | Notes |
|-----------|------------|---------|------|-------|
| Runtime | Python | ≥3.11 | Free | Type hints, match statements |
| Package Manager | UV | Latest | Free | Per technical guide |
| CLI Framework | Click | ^8.0 | Free | Per technical guide |
| Console Output | Rich | ^13.0 | Free | Progress, tables |
| Configuration | Pydantic Settings | ^2.0 | Free | Type-safe config |
| Local Database | SQLite | Built-in | Free | No dependencies |
| Vector Database | Supabase | Free tier | Free | 500MB limit |
| Embeddings | OpenAI API | text-embedding-3-small | ~€0.50 | Batch on ingest |
| Vision API | Groq | llama-3.2-11b-vision | ~€5-15 | Configurable model |
| Object Detection | Ultralytics YOLOv8 | ^8.0 | Free | Auto-download |
| Web Scraping | Playwright | ^1.40 | Free | Dynamic pages |
| HTML Parsing | BeautifulSoup4 | ^4.12 | Free | Robust parsing |
| HTTP Client | httpx | ^0.27 | Free | Async support |
| Image Processing | Pillow | ^10.0 | Free | PNG conversion |
| Camera Capture | OpenCV | ^4.8 | Free | Camera access |
| Groq Client | groq | ^0.5 | Free | Official SDK |

---

## 9. Non-Functional Requirements

| Category | Requirement | Target | Priority |
|----------|-------------|--------|----------|
| Performance | RAG search response | < 2s | Must |
| Performance | YOLO detection | < 1s | Must |
| Performance | Groq vision | < 3s per image | Should |
| Performance | Full identification | < 15s per stamp | Should |
| Reliability | Checkpoint/resume | Required | Must |
| Reliability | Graceful errors | No data loss | Must |
| Maintainability | Logging | Detailed, configurable | Must |
| Maintainability | Configuration | Externalized in .env | Must |
| Scalability | RAG size | ~50,000 stamps | Must |
| Compatibility | OS | Windows 10/11 | Must |
| Compatibility | Python | 3.11+ | Must |
| Security | API keys | .env.keys, gitignored | Must |
| Cost | Supabase | Free tier (<500MB) | Must |
| Cost | Monthly ongoing | < €1/month | Must |

---

## 10. Cost Estimate

### By Scenario

| Scenario | One-Time Cost | Monthly Cost | Notes |
|----------|---------------|--------------|-------|
| Initial Setup | ~€6-16 | €0 | Groq + OpenAI for 50K stamps |
| Ongoing Use | €0 | ~€0.01-0.05 | Occasional identification |

### Cost Breakdown

| Category | Service | One-Time | Monthly | Required |
|----------|---------|----------|---------|----------|
| Vision | Groq API | ~€5-15 | ~€0.01 | Yes |
| Embeddings | OpenAI | ~€0.50 | Negligible | Yes |
| Database | Supabase | Free | Free | Yes |
| Detection | YOLOv8 | Free | Free | Yes |
| **Total** | | **~€6-16** | **< €0.05** | |

---

## 11. Implementation Phases

### Phase 1: Core Infrastructure (4-6 hours)
- Project structure, configuration, database, CLI skeleton, `init` command

### Phase 2: Colnect Scraping (6-8 hours)
- Browser manager, Colnect scraper, `scrape colnect` command

### Phase 3: RAG Pipeline (6-8 hours)
- Groq describer, OpenAI embeddings, Supabase client, indexer, searcher

### Phase 4: Stamp Detection & Identification (6-8 hours)
- Camera capture, YOLO detector, identifier, results display

### Phase 5: Colnect Browser Automation (4-6 hours)
- CDP session, Colnect actions, integration with identification

### Phase 6: LASTDODO Migration (8-10 hours)
- LASTDODO scraper, matcher, mapper, importer, review CLI

### Phase 7: Polish & Documentation (4-6 hours)
- README, CLAUDE.md, help text, edge case testing

**Total estimated effort:** 38-52 hours

**Priority:** Phases 1-5 first (identification capability), Phase 6 can be deferred

---

## 12. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Colnect page structure changes | High | Medium | Modular selectors, easy to update |
| LASTDODO page structure changes | Medium | Low | One-time migration, less critical |
| Supabase free tier exceeded | High | Low | Monitor usage, ~350MB expected |
| Groq API rate limits | Medium | Medium | Implement backoff, respect 30/min |
| YOLOv8 poor stamp detection | Medium | Medium | Could Have: custom training |
| RAG match quality insufficient | Medium | Medium | Tune prompt, try 90b model |
| Chrome CDP issues | Medium | Low | Clear error messages, setup docs |

---

## 13. Appendix

### Default Themes

```
Space, Space Traveling, Astronomy, Rockets, Satellites, Scientists
```

### Condition Mapping

| LASTDODO (Dutch) | Colnect (English) |
|------------------|-------------------|
| Postfris | MNH |
| Ongebruikt | MNH |
| Gestempeld | Used |

### Chrome CDP Startup

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

### Key Dependencies

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [Playwright Python](https://playwright.dev/python/)
- [Supabase Python](https://github.com/supabase-community/supabase-py)
- [Groq Python](https://github.com/groq/groq-python)
- [OpenAI Python](https://github.com/openai/openai-python)

# Claude Command: Update Module Docstring

## Overview

This command updates Python module docstrings to comply with  project documentation standards as defined in `standards/documentation_standards.md`.

## Features

- **Automated Analysis**: Extracts classes, functions, and imports from Python files
- **Standard Compliance**: Generates docstrings following GOVC-advisor standards
- **Smart Detection**: Automatically determines module purpose from directory structure
- **Preservation**: Maintains existing code structure while updating documentation
- **Comprehensive Coverage**: Includes all required sections (Key Features, Architecture, Function Tree, Usage Examples, etc.)

## Usage

```bash
python claude_update_docstring.py <file_path>
```

### Examples

```bash
# Update a document processing handler
python claude_update_docstring.py src/document_processing/openai_handler.py

# Update a web scraping utility
python claude_update_docstring.py src/web_scraping/web_utils/html_utils.py

# Update a RAG module
python claude_update_docstring.py src/rag/chunkers/document_chunker.py
```

## Generated Docstring Structure

The command generates docstrings with these sections (as required by GOVC standards):

1. **Title with separator** - Module name with descriptive subtitle
2. **Brief description** - 1-2 paragraphs explaining module purpose
3. **Key Features** - Bulleted list of main capabilities
4. **Architecture** - High-level explanation of how the module works
5. **Function Tree** - ASCII tree showing classes and functions
6. **Example Usage** - Practical code examples
7. **Configuration Requirements** - Required settings and API keys
8. **Error Handling** - How errors are managed
9. **Dependencies** - Required libraries grouped by type
10. **Performance** - Timing and efficiency notes

## Smart Features

### Module Purpose Detection
The command automatically determines module purpose from directory structure:
- `document_processing/doc_utils/` → "Document processing utilities and helpers"
- `web_scraping/` → "Web scraping functionality"
- `rag/chunkers/` → "RAG document chunking functionality"
- `ui/` → "User interface components"
- `api/` → "API endpoints and services"

### Feature Detection
Automatically detects and documents features based on imports:
- `logging` → "**Logging Integration**: Comprehensive logging with GOVC standards"
- `pathlib` → "**Path Safety**: Cross-platform file path operations"
- `pydantic` → "**Data Validation**: Pydantic models for type safety"
- `asyncio` → "**Async Support**: Asynchronous processing"

### Configuration Requirements
Automatically generates configuration requirements based on detected imports:
- OpenAI imports → OPENAI_API_KEY, OPENAI_MODEL requirements
- Anthropic imports → ANTHROPIC_API_KEY, ANTHROPIC_MODEL requirements
- Supabase imports → SUPABASE_URL, SUPABASE_SERVICE_KEY requirements

### Dependency Categorization
Automatically groups dependencies into:
- **Standard Library** (pathlib, json, logging, etc.)
- **External Dependencies** (openai, anthropic, playwright, etc.)
- **Internal Modules** (src.core, src.document_processing, etc.)

## Example Output

Before:
```python
"""Simple module."""
```

After:
```python
"""
Html Utils - Web Scraping Utilities and Helpers
===============================================

Web scraping utilities and helpers for HTML processing and content extraction.

Key Features:
-------------
- **HTML Processing**: Comprehensive HTML parsing and manipulation
- **Content Extraction**: Structured data extraction from HTML
- **Path Safety**: Cross-platform file path operations using pathlib
- **Logging Integration**: Comprehensive logging with GOVC standards

Architecture:
------------
1. HTML parsing with BeautifulSoup
2. Content extraction and cleaning
3. Markdown conversion
4. File I/O operations

Function Tree:
--------------
```python
html_utils
├── html_to_markdown()                     # Convert HTML to markdown
├── extract_links()                        # Extract all links from HTML
├── clean_html()                           # Clean and normalize HTML
└── save_content()                         # Save content to file
```

Example Usage:
--------------
```python
from web_scraping.web_utils.html_utils import html_to_markdown

# Convert HTML to markdown
markdown = html_to_markdown(html_content)
print(markdown)
```

Configuration Requirements:
--------------------------
- No special configuration required

Error Handling:
---------------
- Comprehensive exception handling with logging
- Graceful degradation for malformed HTML
- Input validation and type checking

Dependencies:
-------------
### Standard Library
- pathlib: Built-in Python library
- logging: Built-in Python library

### External Dependencies
- beautifulsoup4: External package (install via pip)
- lxml: External package (install via pip)

Performance:
------------
- Optimized for HTML parsing efficiency
- Memory-efficient processing for large documents
- Proper resource cleanup and management

---
*Generated with GOVC-advisor documentation standards*
"""
```

## Integration with GOVC Standards

This command ensures full compliance with:

1. **Documentation Standards** (`standards/documentation_standards.md`)
2. **Configuration Management** (uses `core.GOVC_config`)
3. **Logging Standards** (uses standard logging patterns)
4. **Path Safety** (uses `pathlib.Path` operations)
5. **Type Hints** (includes proper type annotations)

## Benefits

- ✅ **Consistency**: All modules follow the same documentation format
- ✅ **Completeness**: All required sections are included
- ✅ **Maintainability**: Easy to understand module structure and purpose
- ✅ **Standards Compliance**: Fully aligned with GOVC-advisor project standards
- ✅ **Time Saving**: Automated generation saves manual documentation effort
- ✅ **Quality**: Professional, well-structured documentation

## Error Handling

The command includes comprehensive error handling:
- **Syntax Errors**: Detects and reports Python syntax issues
- **File Not Found**: Validates file existence before processing
- **Import Issues**: Handles missing modules gracefully
- **AST Parsing**: Robust parsing of Python code structure

## Technical Implementation

- **AST Parsing**: Uses Python's `ast` module for accurate code analysis
- **Path Analysis**: Leverages `pathlib.Path` for cross-platform compatibility
- **String Manipulation**: Efficient string operations for docstring generation
- **File I/O**: Safe file reading and writing with proper encoding

## Future Enhancements

Potential improvements for future versions:
- **Function Docstrings**: Update individual function docstrings to Google style
- **Type Detection**: More sophisticated type analysis for better documentation
- **Cross-References**: Add links to related modules and documentation
- **Validation**: Verify that generated docstrings meet all standard requirements
- **Batch Processing**: Support updating multiple files at once

---

*This command is part of the GOVC-advisor project's documentation automation toolkit.*

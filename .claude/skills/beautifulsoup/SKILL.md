---
name: beautifulsoup
description: HTML and XML parsing for web scraping with BeautifulSoup. Use when scraping static websites, parsing HTML/XML, extracting data from web pages, or when user mentions BeautifulSoup, bs4, web scraping, or HTML parsing.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# BeautifulSoup Web Scraping

## Overview

BeautifulSoup is a Python library for parsing HTML and XML documents. It creates a parse tree for parsed pages that can be used to extract data easily.

## When to Use This Skill

- Scraping static HTML websites
- Parsing HTML/XML documents
- Extracting text, links, and data from web pages
- Cleaning and transforming HTML content
- Processing local HTML files

**Note:** For JavaScript-rendered sites, use Playwright instead.

## Project Setup

### Installation

```bash
# Using pip
pip install beautifulsoup4 requests lxml

# Using uv
uv add beautifulsoup4 requests lxml
```

### Project Structure

```
scraper/
├── main.py              # Main scraper script
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py   # Base parser class
│   └── product_parser.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── data/
│   └── output.json
└── requirements.txt
```

## Core Patterns

### Basic Scraping

```python
import requests
from bs4 import BeautifulSoup

def scrape_page(url: str) -> BeautifulSoup:
    """Fetch and parse a webpage."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")

# Usage
soup = scrape_page("https://example.com")
title = soup.title.string
```

### Parsing Local Files

```python
from bs4 import BeautifulSoup
from pathlib import Path

def parse_file(filepath: str) -> BeautifulSoup:
    """Parse a local HTML file."""
    content = Path(filepath).read_text(encoding="utf-8")
    return BeautifulSoup(content, "lxml")

soup = parse_file("page.html")
```

## Element Selection

### Find Methods

```python
# Single element
element = soup.find("div", class_="container")
element = soup.find("a", href=True)
element = soup.find("input", {"type": "text", "name": "email"})

# Multiple elements
elements = soup.find_all("p")
elements = soup.find_all("a", class_="link")
elements = soup.find_all(["h1", "h2", "h3"])  # Multiple tags

# Limit results
elements = soup.find_all("li", limit=5)
```

### CSS Selectors

```python
# Single element
element = soup.select_one("div.container")
element = soup.select_one("#main-content")
element = soup.select_one("article > h1")

# Multiple elements
elements = soup.select("div.product")
elements = soup.select("ul.menu li a")
elements = soup.select("[data-id]")  # Attribute selector
elements = soup.select("a[href^='https']")  # Starts with
elements = soup.select("img[src$='.png']")  # Ends with
```

### Navigation

```python
# Parent/children
parent = element.parent
children = element.children  # Generator
children_list = list(element.children)

# Siblings
next_sibling = element.find_next_sibling()
prev_sibling = element.find_previous_sibling()
all_siblings = element.find_next_siblings()

# Descendants
descendants = element.descendants  # All nested elements

# Navigation chain
article = soup.select_one("article")
first_p = article.find("p")
```

## Data Extraction

### Text Content

```python
# Get text
text = element.get_text()
text = element.get_text(strip=True)  # Remove whitespace
text = element.get_text(separator=" ")  # Join with separator
text = element.string  # Direct string child only

# All text from page
all_text = soup.get_text(separator="\n", strip=True)
```

### Attributes

```python
# Get attributes
href = link.get("href")
href = link["href"]  # Raises KeyError if missing
src = img.get("src", "")  # With default

# Check attribute exists
if link.has_attr("href"):
    print(link["href"])

# Get all attributes
attrs = element.attrs  # Dict of all attributes
classes = element.get("class", [])  # Class is always a list
```

### Extracting Structured Data

```python
def extract_products(soup: BeautifulSoup) -> list[dict]:
    """Extract product data from page."""
    products = []

    for item in soup.select(".product-card"):
        product = {
            "name": item.select_one(".title").get_text(strip=True),
            "price": item.select_one(".price").get_text(strip=True),
            "url": item.select_one("a")["href"],
            "image": item.select_one("img").get("src", ""),
            "rating": item.select_one(".rating").get_text(strip=True)
            if item.select_one(".rating") else None
        }
        products.append(product)

    return products
```

## Advanced Patterns

### Custom Filters

```python
# Function filter
def has_data_id(tag):
    return tag.has_attr("data-id")

elements = soup.find_all(has_data_id)

# Lambda filter
elements = soup.find_all(lambda tag: tag.name == "div" and "container" in tag.get("class", []))

# Regex filter
import re
elements = soup.find_all("a", href=re.compile(r"^/products/"))
elements = soup.find_all(string=re.compile(r"\$\d+"))
```

### Modifying HTML

```python
# Modify content
element.string = "New text"
element["class"] = ["new-class"]
element["href"] = "/new-url"

# Add/remove attributes
del element["style"]
element["data-new"] = "value"

# Remove elements
element.decompose()  # Remove from tree
element.extract()    # Remove but keep reference

# Replace elements
new_tag = soup.new_tag("span")
new_tag.string = "Replacement"
element.replace_with(new_tag)

# Wrap elements
wrapper = soup.new_tag("div", class_="wrapper")
element.wrap(wrapper)
```

### Handling Encoding

```python
# Parse with encoding
soup = BeautifulSoup(content, "lxml", from_encoding="utf-8")

# Get original encoding
print(soup.original_encoding)

# Output with encoding
html_str = soup.prettify(encoding="utf-8")
```

## Scraping Patterns

### Pagination Handler

```python
def scrape_all_pages(base_url: str) -> list[dict]:
    """Scrape all pages of results."""
    all_items = []
    page = 1

    while True:
        url = f"{base_url}?page={page}"
        soup = scrape_page(url)

        items = extract_items(soup)
        if not items:
            break

        all_items.extend(items)

        # Check for next page
        next_link = soup.select_one("a.next-page")
        if not next_link:
            break

        page += 1

    return all_items
```

### Rate-Limited Scraper

```python
import time
import random

class RateLimitedScraper:
    def __init__(self, delay_range: tuple = (1, 3)):
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"
        })

    def fetch(self, url: str) -> BeautifulSoup:
        """Fetch with rate limiting."""
        time.sleep(random.uniform(*self.delay_range))
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    def scrape_urls(self, urls: list[str]) -> list[BeautifulSoup]:
        """Scrape multiple URLs with rate limiting."""
        return [self.fetch(url) for url in urls]
```

### Table Parser

```python
def parse_table(table) -> list[dict]:
    """Convert HTML table to list of dicts."""
    headers = [th.get_text(strip=True) for th in table.select("thead th")]

    rows = []
    for tr in table.select("tbody tr"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        row = dict(zip(headers, cells))
        rows.append(row)

    return rows

# Usage
table = soup.select_one("table.data")
data = parse_table(table)
```

### Link Extractor

```python
from urllib.parse import urljoin, urlparse

def extract_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Extract all links with metadata."""
    links = []

    for a in soup.select("a[href]"):
        href = a["href"]
        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)

        links.append({
            "text": a.get_text(strip=True),
            "href": absolute_url,
            "is_external": parsed.netloc != urlparse(base_url).netloc,
            "is_anchor": href.startswith("#")
        })

    return links
```

## Parser Comparison

| Parser | Speed | Lenient | Features |
|--------|-------|---------|----------|
| `html.parser` | Moderate | Yes | Built-in, no deps |
| `lxml` | Fast | Yes | Full XPath support |
| `lxml-xml` | Fast | No | XML only |
| `html5lib` | Slow | Very | Parses like browser |

```python
# Recommended for most cases
soup = BeautifulSoup(html, "lxml")

# For malformed HTML
soup = BeautifulSoup(html, "html5lib")

# For XML
soup = BeautifulSoup(xml, "lxml-xml")
```

## Best Practices

1. **Use appropriate parser** - `lxml` for speed, `html5lib` for bad HTML
2. **Handle missing elements** - Use `.get()` and check for `None`
3. **Add delays** - Respect rate limits and robots.txt
4. **Set User-Agent** - Identify your scraper
5. **Handle errors** - Wrap requests in try/except
6. **Cache responses** - Avoid repeated requests during development
7. **Use sessions** - Reuse connections for efficiency
8. **Validate data** - Check extracted data is complete

## Common Issues

| Issue | Solution |
|-------|----------|
| Empty results | Check selector, inspect actual HTML |
| Encoding errors | Specify encoding or use `response.content` |
| Missing dynamic content | Use Playwright for JS-rendered pages |
| 403 Forbidden | Add headers, check robots.txt |
| Rate limited | Add delays, use rotating proxies |
| Memory issues | Process pages one at a time |

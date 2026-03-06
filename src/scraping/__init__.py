"""Web scraping module for the Stamp Collection Toolset.

This module handles automated data extraction from stamp catalog websites using
Playwright for browser automation and BeautifulSoup for HTML parsing.

Modules
-------
browser.py
    BrowserManager: Manages Playwright browser lifecycle, handles page navigation,
    screenshot capture, and session persistence. Supports headless and headed modes.

colnect.py
    ColnectScraper: Scrapes stamp catalog data from Colnect. Extracts stamp ID, title,
    country, year, themes, image URLs, and catalog codes (Michel, Scott, etc.).
    Supports filtering by theme, country, and year. Includes resume capability
    for interrupted scrapes.

lastdodo.py (planned)
    LastdodoScraper: Scrapes user collection from LASTDODO for migration.
    Requires logged-in Chrome session via CDP connection.

Key Exports
-----------
- BrowserManager: Browser lifecycle and page automation
- ColnectScraper: Colnect catalog data extraction
"""

from src.scraping.browser import BrowserManager
from src.scraping.colnect import ColnectScraper

__all__ = [
    "BrowserManager",
    "ColnectScraper",
]

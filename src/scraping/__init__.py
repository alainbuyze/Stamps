"""Web scraping module for Stamp Collection Toolset.

Components:
- BrowserManager: Playwright browser management for scraping
- ColnectScraper: Scrapes stamp data from Colnect catalog
- LastdodoScraper: Scrapes user collection from LASTDODO (Phase 6)
"""

from src.scraping.browser import BrowserManager
from src.scraping.colnect import ColnectScraper

__all__ = [
    "BrowserManager",
    "ColnectScraper",
]

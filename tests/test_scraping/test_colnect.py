"""Tests for Colnect scraper."""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.scraping.colnect import ColnectScraper, ScrapeCheckpoint
from src.core.errors import ExtractionError


class TestScrapeCheckpoint:
    """Tests for ScrapeCheckpoint dataclass."""

    def test_to_dict(self):
        """Test checkpoint serialization."""
        checkpoint = ScrapeCheckpoint(
            theme="Space",
            page_number=5,
            processed_urls=["url1", "url2"],
            total_scraped=42,
            last_updated="2024-01-01T00:00:00",
        )

        result = checkpoint.to_dict()

        assert result["theme"] == "Space"
        assert result["page_number"] == 5
        assert result["processed_urls"] == ["url1", "url2"]
        assert result["total_scraped"] == 42

    def test_from_dict(self):
        """Test checkpoint deserialization."""
        data = {
            "theme": "Astronomy",
            "page_number": 3,
            "processed_urls": ["url1"],
            "total_scraped": 100,
            "last_updated": "2024-01-01T00:00:00",
        }

        checkpoint = ScrapeCheckpoint.from_dict(data)

        assert checkpoint.theme == "Astronomy"
        assert checkpoint.page_number == 3
        assert checkpoint.processed_urls == ["url1"]
        assert checkpoint.total_scraped == 100

    def test_from_dict_defaults(self):
        """Test checkpoint deserialization with missing fields."""
        data = {}

        checkpoint = ScrapeCheckpoint.from_dict(data)

        assert checkpoint.theme == ""
        assert checkpoint.page_number == 1
        assert checkpoint.processed_urls == []
        assert checkpoint.total_scraped == 0


class TestColnectScraperCheckpoint:
    """Tests for checkpoint management."""

    def test_save_checkpoint(self, temp_checkpoint):
        """Test saving checkpoint to file."""
        scraper = ColnectScraper.__new__(ColnectScraper)
        scraper.checkpoint_file = temp_checkpoint

        checkpoint = ScrapeCheckpoint(
            theme="Space",
            page_number=5,
            processed_urls=["url1"],
            total_scraped=10,
        )

        scraper.save_checkpoint(checkpoint)

        assert temp_checkpoint.exists()
        with open(temp_checkpoint) as f:
            data = json.load(f)
        assert data["theme"] == "Space"
        assert data["page_number"] == 5

    def test_load_checkpoint(self, temp_checkpoint):
        """Test loading checkpoint from file."""
        # Create checkpoint file
        data = {
            "theme": "Rockets",
            "page_number": 2,
            "processed_urls": [],
            "total_scraped": 5,
            "last_updated": "2024-01-01T00:00:00",
        }
        temp_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_checkpoint, "w") as f:
            json.dump(data, f)

        scraper = ColnectScraper.__new__(ColnectScraper)
        scraper.checkpoint_file = temp_checkpoint

        loaded = scraper.load_checkpoint()

        assert loaded.theme == "Rockets"
        assert loaded.page_number == 2

    def test_load_checkpoint_missing_file(self, temp_checkpoint):
        """Test loading checkpoint when file doesn't exist."""
        scraper = ColnectScraper.__new__(ColnectScraper)
        scraper.checkpoint_file = temp_checkpoint

        result = scraper.load_checkpoint()

        assert result is None

    def test_clear_checkpoint(self, temp_checkpoint):
        """Test clearing checkpoint file."""
        temp_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        temp_checkpoint.write_text("{}")

        scraper = ColnectScraper.__new__(ColnectScraper)
        scraper.checkpoint_file = temp_checkpoint

        scraper.clear_checkpoint()

        assert not temp_checkpoint.exists()


class TestColnectScraperURLs:
    """Tests for URL generation."""

    def test_get_theme_url_page_1(self):
        """Test theme URL for first page."""
        scraper = ColnectScraper.__new__(ColnectScraper)

        url = scraper.get_theme_url("space", 1)

        assert url == "https://colnect.com/en/stamps/list/theme/space"

    def test_get_theme_url_page_n(self):
        """Test theme URL for subsequent pages."""
        scraper = ColnectScraper.__new__(ColnectScraper)

        url = scraper.get_theme_url("astronomy", 5)

        assert url == "https://colnect.com/en/stamps/list/theme/astronomy/page/5"


class TestColnectScraperExtraction:
    """Tests for HTML extraction methods."""

    def test_extract_title_from_h1(self):
        """Test title extraction from h1 element."""
        from bs4 import BeautifulSoup

        html = '<html><body><h1 class="item_name">Apollo 11 Moon Landing</h1></body></html>'
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        title = scraper._extract_title(soup)

        assert title == "Apollo 11 Moon Landing"

    def test_extract_title_missing_raises(self):
        """Test that missing title raises error."""
        from bs4 import BeautifulSoup

        html = "<html><body><p>No title here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)

        with pytest.raises(ExtractionError, match="Cannot extract title"):
            scraper._extract_title(soup)

    def test_extract_country_from_link(self):
        """Test country extraction from link."""
        from bs4 import BeautifulSoup

        html = '<html><body><a href="/en/stamps/country/usa">United States</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        country = scraper._extract_country(soup)

        assert country == "United States"

    def test_extract_country_from_table(self):
        """Test country extraction from metadata table."""
        from bs4 import BeautifulSoup

        html = """
        <html><body>
        <table>
            <tr><th>Country</th><td>Germany</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        country = scraper._extract_country(soup)

        assert country == "Germany"

    def test_extract_year_from_table(self):
        """Test year extraction from metadata table."""
        from bs4 import BeautifulSoup

        html = """
        <html><body>
        <table>
            <tr><th>Year of Issue</th><td>1969</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        year = scraper._extract_year(soup)

        assert year == 1969

    def test_extract_year_from_text(self):
        """Test year extraction from page text."""
        from bs4 import BeautifulSoup

        html = "<html><body>Issued: 2021</body></html>"
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        year = scraper._extract_year(soup)

        assert year == 2021

    def test_extract_image_url(self):
        """Test image URL extraction."""
        from bs4 import BeautifulSoup

        html = '<html><body><img class="item_image" src="/images/stamp123.jpg"></body></html>'
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        image_url = scraper._extract_image_url(soup)

        assert image_url == "https://colnect.com/images/stamp123.jpg"

    def test_extract_themes(self):
        """Test themes extraction."""
        from bs4 import BeautifulSoup

        html = """
        <html><body>
        <a href="/en/stamps/theme/space">Space</a>
        <a href="/en/stamps/theme/rockets">Rockets</a>
        <a href="/en/stamps/something/else">Not a theme</a>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        themes = scraper._extract_themes(soup)

        assert "Space" in themes
        assert "Rockets" in themes

    def test_extract_catalog_codes(self):
        """Test catalog codes extraction."""
        from bs4 import BeautifulSoup

        html = """
        <html><body>
        <table>
            <tr><th>Michel</th><td>123A</td></tr>
            <tr><th>Scott</th><td>456</td></tr>
            <tr><th>Stanley Gibbons</th><td>789</td></tr>
            <tr><th>Yvert</th><td>-</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        scraper = ColnectScraper.__new__(ColnectScraper)
        codes = scraper._extract_catalog_codes(soup)

        assert codes.get("michel") == "123A"
        assert codes.get("scott") == "456"
        assert codes.get("sg") == "789"
        assert "yvert" not in codes  # "-" should be ignored


class TestColnectScraperIntegration:
    """Integration tests with mocked browser."""

    @pytest.mark.asyncio
    async def test_scrape_stamp_page(self):
        """Test scraping a single stamp page."""
        # Create mock browser
        mock_browser = MagicMock()
        mock_browser.goto_and_get_content = AsyncMock(
            return_value="""
            <html>
            <body>
                <h1 class="item_name">Test Stamp</h1>
                <a href="/en/stamps/country/usa">United States</a>
                <table>
                    <tr><th>Year</th><td>2020</td></tr>
                    <tr><th>Michel</th><td>TEST123</td></tr>
                </table>
                <a href="/en/stamps/theme/space">Space</a>
                <img class="item_image" src="/images/test.jpg">
            </body>
            </html>
            """
        )

        # Create scraper with mock
        scraper = ColnectScraper.__new__(ColnectScraper)
        scraper._browser = mock_browser

        # Create mock page
        mock_page = MagicMock()

        # Test
        stamp = await scraper.scrape_stamp_page(
            mock_page, "https://colnect.com/en/stamps/stamp/12345-Test"
        )

        assert stamp.colnect_id == "12345"
        assert stamp.title == "Test Stamp"
        assert stamp.country == "United States"
        assert stamp.year == 2020
        assert stamp.catalog_codes.get("michel") == "TEST123"
        assert "Space" in stamp.themes

    @pytest.mark.asyncio
    async def test_scrape_stamp_page_invalid_url(self):
        """Test that invalid URL raises error."""
        mock_browser = MagicMock()
        mock_browser.goto_and_get_content = AsyncMock(return_value="<html></html>")

        scraper = ColnectScraper.__new__(ColnectScraper)
        scraper._browser = mock_browser

        mock_page = MagicMock()

        with pytest.raises(ExtractionError, match="Cannot extract stamp ID"):
            await scraper.scrape_stamp_page(mock_page, "https://colnect.com/invalid")

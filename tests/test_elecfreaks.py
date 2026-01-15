"""Tests for Elecfreaks adapter."""

from bs4 import BeautifulSoup

from src.sources.elecfreaks import ElecfreaksAdapter


def test_can_handle_elecfreaks_wiki():
    """Test that adapter handles Elecfreaks Wiki URLs."""
    adapter = ElecfreaksAdapter()

    assert adapter.can_handle("https://wiki.elecfreaks.com/en/some/page")
    assert adapter.can_handle("https://wiki.elecfreaks.com/en/microbit/building-blocks")
    assert adapter.can_handle("http://wiki.elecfreaks.com/page")


def test_cannot_handle_other_urls():
    """Test that adapter rejects non-Elecfreaks URLs."""
    adapter = ElecfreaksAdapter()

    assert not adapter.can_handle("https://example.com")
    assert not adapter.can_handle("https://github.com/elecfreaks")
    assert not adapter.can_handle("https://google.com")


def test_extract_title_from_h1():
    """Test title extraction from h1 element."""
    adapter = ElecfreaksAdapter()

    html = """
    <html>
    <body>
    <article>
        <h1>Test Tutorial Title</h1>
        <p>Some content</p>
    </article>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    content = adapter.extract(soup, "https://wiki.elecfreaks.com/test")

    assert content.title == "Test Tutorial Title"


def test_extract_images():
    """Test image extraction from content."""
    adapter = ElecfreaksAdapter()

    html = """
    <html>
    <body>
    <article>
        <h1>Test</h1>
        <img src="https://example.com/image1.png" alt="Image 1" />
        <img src="/relative/image2.jpg" alt="Image 2" />
    </article>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    content = adapter.extract(soup, "https://wiki.elecfreaks.com/test")

    assert len(content.images) == 2
    assert content.images[0]["src"] == "https://example.com/image1.png"
    assert content.images[0]["alt"] == "Image 1"


def test_extract_removes_navigation():
    """Test that navigation elements are removed."""
    adapter = ElecfreaksAdapter()

    html = """
    <html>
    <body>
    <nav class="navbar">Navigation</nav>
    <article>
        <h1>Title</h1>
        <p>Content</p>
    </article>
    <footer>Footer</footer>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    content = adapter.extract(soup, "https://wiki.elecfreaks.com/test")

    # Should have found content
    assert content.title == "Title"
    assert content.metadata["source"] == "elecfreaks"


def test_extract_metadata():
    """Test metadata extraction."""
    adapter = ElecfreaksAdapter()

    html = """
    <html>
    <head>
        <meta name="description" content="A test tutorial about electronics" />
    </head>
    <body>
    <article>
        <h1>Test</h1>
    </article>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    content = adapter.extract(soup, "https://wiki.elecfreaks.com/test")

    assert content.metadata["description"] == "A test tutorial about electronics"
    assert content.metadata["url"] == "https://wiki.elecfreaks.com/test"

"""Verify the changes to cli.py and elecfreaks.py work correctly."""

import sys
sys.path.insert(0, '.')

from bs4 import BeautifulSoup
from src.cli import get_project_filename
from src.sources.elecfreaks import ElecfreaksAdapter


def test_get_project_filename():
    """Test all filename generation cases."""
    print("Testing get_project_filename...")

    # Original functionality (should still work)
    result = get_project_filename("01", "The Mechanical Shrimp")
    assert result == "Project 01 - The Mechanical Shrimp", f"Basic test failed: {result}"
    print(f"  ✓ Basic: {result}")

    result = get_project_filename("12", "Café au lait")
    assert result == "Project 12 - Cafe au lait", f"Accents test failed: {result}"
    print(f"  ✓ Accents: {result}")

    result = get_project_filename("05", "Test: Special! Chars?")
    assert result == "Project 05 - Test Special Chars", f"Special chars test failed: {result}"
    print(f"  ✓ Special chars: {result}")

    # New functionality (fixes)
    result = get_project_filename("01", "3.Project 01: De motorfiets")
    assert result == "Project 01 - De motorfiets", f"Leading number prefix test failed: {result}"
    print(f"  ✓ Leading number prefix: {result}")

    result = get_project_filename("01", "De motorfiets#")
    assert result == "Project 01 - De motorfiets", f"Trailing hash test failed: {result}"
    print(f"  ✓ Trailing hash: {result}")

    result = get_project_filename("01", "3.Project 01: De motorfiets#")
    assert result == "Project 01 - De motorfiets", f"Both prefix and hash test failed: {result}"
    print(f"  ✓ Both prefix and hash: {result}")

    result = get_project_filename("05", "Project 05: Robot Arm")
    assert result == "Project 05 - Robot Arm", f"Project prefix only test failed: {result}"
    print(f"  ✓ Project prefix only: {result}")

    result = get_project_filename("12", "Les 12: Sensor Demo")
    assert result == "Project 12 - Sensor Demo", f"Les prefix test failed: {result}"
    print(f"  ✓ Les prefix: {result}")

    print("All get_project_filename tests passed!\n")


def test_elecfreaks_image_extraction():
    """Test that relative image URLs are updated to absolute in HTML."""
    print("Testing ElecfreaksAdapter image extraction...")

    adapter = ElecfreaksAdapter()

    html = """
    <html>
    <body>
    <article>
        <h1>Test</h1>
        <p>Intro paragraph</p>
        <img src="../../_images/step-01.png" alt="Step 1" />
        <img src="../images/step-02.png" alt="Step 2" />
    </article>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    content = adapter.extract(soup, "https://wiki.elecfreaks.com/en/microbit/kit/case_01")

    # Images list should have absolute URLs
    assert len(content.images) == 2, f"Expected 2 images, got {len(content.images)}"
    assert content.images[0]["src"].startswith("https://"), f"Image 0 not absolute: {content.images[0]['src']}"
    assert content.images[1]["src"].startswith("https://"), f"Image 1 not absolute: {content.images[1]['src']}"
    print(f"  ✓ Images list has absolute URLs")
    print(f"    Image 0: {content.images[0]['src']}")
    print(f"    Image 1: {content.images[1]['src']}")

    # The img tags in the soup should also be updated to absolute URLs
    img_tags = soup.find_all("img")
    assert img_tags[0]["src"].startswith("https://"), f"Img tag 0 not updated: {img_tags[0]['src']}"
    assert img_tags[1]["src"].startswith("https://"), f"Img tag 1 not updated: {img_tags[1]['src']}"
    print(f"  ✓ HTML img tags updated to absolute URLs")

    # Verify the URLs match
    assert img_tags[0]["src"] == content.images[0]["src"], "Img tag 0 doesn't match images list"
    assert img_tags[1]["src"] == content.images[1]["src"], "Img tag 1 doesn't match images list"
    print(f"  ✓ HTML img tags match images list")

    print("All ElecfreaksAdapter tests passed!\n")


if __name__ == "__main__":
    try:
        test_get_project_filename()
        test_elecfreaks_image_extraction()
        print("=" * 50)
        print("All tests passed! Changes are working correctly.")
        print("=" * 50)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

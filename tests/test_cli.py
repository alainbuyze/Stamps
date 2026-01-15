"""Tests for CLI interface."""

from click.testing import CliRunner

from src.cli import cli, get_output_filename, slugify


def test_slugify_basic():
    """Test basic slugification."""
    assert slugify("Hello World") == "hello-world"
    assert slugify("Test_Case_01") == "test-case-01"
    assert slugify("UPPERCASE") == "uppercase"


def test_slugify_special_chars():
    """Test slugification removes special characters."""
    assert slugify("Hello! World?") == "hello-world"
    assert slugify("test@case#01") == "testcase01"


def test_slugify_multiple_hyphens():
    """Test slugification normalizes multiple hyphens."""
    assert slugify("test---case") == "test-case"
    assert slugify("  test  case  ") == "test-case"


def test_get_output_filename_from_url():
    """Test filename extraction from URL."""
    url = "https://wiki.elecfreaks.com/en/case_01_test"
    filename = get_output_filename(url, "Some Title")

    assert "case" in filename.lower()


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "CoderDojo Guide Generator" in result.output


def test_cli_version():
    """Test CLI version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_sources():
    """Test CLI sources command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["sources"])

    assert result.exit_code == 0
    assert "elecfreaks" in result.output.lower()


def test_cli_generate_missing_url():
    """Test CLI generate command requires URL."""
    runner = CliRunner()
    result = runner.invoke(cli, ["generate"])

    assert result.exit_code != 0
    assert "url" in result.output.lower()

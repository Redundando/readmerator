"""Basic tests for readmerator."""

from pathlib import Path
from readmerator.parser import parse_requirements_txt


def test_parse_requirements():
    """Test parsing a simple requirements file."""
    test_file = Path("test_req.txt")
    test_file.write_text("requests>=2.0.0\nclick==8.0.0\n# comment\naiohttp")
    
    packages = parse_requirements_txt(test_file)
    
    assert "requests" in packages
    assert "click" in packages
    assert "aiohttp" in packages
    assert len(packages) == 3
    
    test_file.unlink()


def test_parse_empty_file():
    """Test parsing empty requirements file."""
    test_file = Path("empty_req.txt")
    test_file.write_text("# only comments\n\n")
    
    packages = parse_requirements_txt(test_file)
    
    assert len(packages) == 0
    
    test_file.unlink()

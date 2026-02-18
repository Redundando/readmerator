"""Parse Python dependency files."""

import re
from pathlib import Path
from typing import List, Set


def parse_requirements_txt(file_path: Path) -> List[str]:
    """Parse requirements.txt and extract package names."""
    packages: Set[str] = set()
    
    if not file_path.exists():
        return []
    
    content = file_path.read_text(encoding="utf-8")
    
    for line in content.splitlines():
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue
        
        # Skip -r, -e, --hash, etc.
        if line.startswith("-"):
            continue
        
        # Extract package name (before any version specifier)
        match = re.match(r"^([a-zA-Z0-9_-]+)", line)
        if match:
            packages.add(match.group(1).lower())
    
    return sorted(packages)


def find_dependency_file(directory: Path) -> Path | None:
    """Find requirements.txt in directory."""
    req_file = directory / "requirements.txt"
    if req_file.exists():
        return req_file
    return None

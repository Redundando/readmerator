"""Core functionality for fetching package READMEs."""

import asyncio
import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import aiohttp


async def fetch_pypi_metadata(session: aiohttp.ClientSession, package: str) -> Optional[Dict]:
    """Fetch package metadata from PyPI."""
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception:
        pass
    return None


async def fetch_github_readme(session: aiohttp.ClientSession, repo_url: str) -> Optional[str]:
    """Fetch README from GitHub repository."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        return None
    
    owner, repo = match.groups()
    repo = repo.rstrip("/").removesuffix(".git")
    
    for branch in ["main", "master"]:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception:
            continue
    return None


async def fetch_package_readme(session: aiohttp.ClientSession, package: str) -> Optional[tuple[str, str, str, str]]:
    """Fetch README for a package. Returns (content, version, source_url, source_type)."""
    metadata = await fetch_pypi_metadata(session, package)
    if not metadata:
        return None
    
    info = metadata.get("info", {})
    version = info.get("version", "unknown")
    
    # Try PyPI long_description first
    description = info.get("description", "")
    if description and len(description) > 100:
        pypi_url = f"https://pypi.org/project/{package}/"
        return (description, version, pypi_url, "PyPI")
    
    # Try GitHub README
    project_urls = info.get("project_urls", {})
    for key in ["Source", "Homepage", "Repository", "GitHub"]:
        url = project_urls.get(key, "")
        if "github.com" in url:
            readme = await fetch_github_readme(session, url)
            if readme:
                return (readme, version, url, "GitHub")
    
    # Fallback to short description
    summary = info.get("summary", "")
    if summary:
        pypi_url = f"https://pypi.org/project/{package}/"
        return (f"# {package}\n\n{summary}\n\nSee: {pypi_url}", version, pypi_url, "PyPI summary")
    
    return None


def create_readme_content(package: str, content: str, version: str, source_url: str) -> str:
    """Create formatted README with metadata header."""
    header = f"""---
Package: {package}
Version: {version}
Source: {source_url}
Fetched: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
---

"""
    return header + content


async def fetch_all_readmes(packages: List[str], output_dir: Path, verbose: bool = False) -> Dict[str, bool]:
    """Fetch READMEs for all packages. Returns dict of package: success."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for package in packages:
            tasks.append(fetch_and_save(session, package, output_dir, verbose))
        
        results_list = await asyncio.gather(*tasks)
        for package, success in results_list:
            results[package] = success
    
    return results


async def fetch_and_save(session: aiohttp.ClientSession, package: str, output_dir: Path, verbose: bool) -> tuple[str, bool]:
    """Fetch and save README for a single package."""
    if verbose:
        print(f"Fetching {package}...")
    
    result = await fetch_package_readme(session, package)
    if not result:
        if verbose:
            print(f"  ✗ {package}: Failed to fetch")
        return (package, False)
    
    content, version, source_url, source_type = result
    readme_content = create_readme_content(package, content, version, source_url)
    
    output_file = output_dir / f"{package}.md"
    output_file.write_text(readme_content, encoding="utf-8")
    
    if verbose:
        print(f"  ✓ {package}: Saved ({len(content)} bytes) from {source_type}")
    
    return (package, True)

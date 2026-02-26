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


async def fetch_npm_readme(session: aiohttp.ClientSession, package: str) -> Optional[tuple[str, str, str, str]]:
    """Fetch README for npm package. Returns (content, version, source_url, source_type)."""
    url = f"https://registry.npmjs.org/{package}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            
            version = data.get("dist-tags", {}).get("latest", "unknown")
            readme = data.get("readme", "")
            npm_url = f"https://www.npmjs.com/package/{package}"
            
            if readme and len(readme) > 50:
                return (readme, version, npm_url, "npm")
            
            # Fallback to description
            description = data.get("description", "")
            if description:
                return (f"# {package}\n\n{description}\n\nSee: {npm_url}", version, npm_url, "npm summary")
    except Exception:
        pass
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


async def fetch_all_readmes(packages: Dict[str, List[str]], output_dir: Path, verbose: bool = False) -> Dict[str, Dict[str, bool]]:
    """Fetch READMEs for all packages. Returns dict of ecosystem: {package: success}."""
    results = {"python": {}, "npm": {}}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Python packages
        python_dir = output_dir / "python"
        for package in packages.get("python", []):
            tasks.append(fetch_and_save_python(session, package, python_dir, verbose))
        
        # npm packages
        npm_dir = output_dir / "npm"
        for package in packages.get("npm", []):
            tasks.append(fetch_and_save_npm(session, package, npm_dir, verbose))
        
        results_list = await asyncio.gather(*tasks)
        for ecosystem, package, success in results_list:
            results[ecosystem][package] = success
    
    return results


async def fetch_and_save_python(session: aiohttp.ClientSession, package: str, output_dir: Path, verbose: bool) -> tuple[str, str, bool]:
    """Fetch and save README for a Python package."""
    if verbose:
        print(f"Fetching {package}...")
    
    result = await fetch_package_readme(session, package)
    if not result:
        if verbose:
            print(f"  ✗ {package}: Failed to fetch")
        return ("python", package, False)
    
    content, version, source_url, source_type = result
    readme_content = create_readme_content(package, content, version, source_url)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{package}.md"
    output_file.write_text(readme_content, encoding="utf-8")
    
    if verbose:
        print(f"  ✓ {package}: Saved ({len(content)} bytes) from {source_type}")
    
    return ("python", package, True)


async def fetch_and_save_npm(session: aiohttp.ClientSession, package: str, output_dir: Path, verbose: bool) -> tuple[str, str, bool]:
    """Fetch and save README for an npm package."""
    if verbose:
        print(f"Fetching {package}...")
    
    result = await fetch_npm_readme(session, package)
    if not result:
        if verbose:
            print(f"  ✗ {package}: Failed to fetch")
        return ("npm", package, False)
    
    content, version, source_url, source_type = result
    readme_content = create_readme_content(package, content, version, source_url)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    # Handle scoped packages (@org/package)
    safe_name = package.replace("/", "_").replace("@", "")
    output_file = output_dir / f"{safe_name}.md"
    output_file.write_text(readme_content, encoding="utf-8")
    
    if verbose:
        print(f"  ✓ {package}: Saved ({len(content)} bytes) from {source_type}")
    
    return ("npm", package, True)


async def fetch_readme_from_url(url: str, output_dir: Path, custom_name: Optional[str] = None, verbose: bool = False) -> bool:
    """Fetch README from a custom URL."""
    import re
    from urllib.parse import urlparse
    
    async with aiohttp.ClientSession() as session:
        try:
            # Determine if it's a GitHub repo URL or direct README URL
            if "github.com" in url and "/blob/" not in url and not url.endswith(".md"):
                # Convert GitHub repo URL to raw README URL
                readme_url = await _get_github_readme_url(session, url)
                if not readme_url:
                    print(f"✗ Could not find README in GitHub repo: {url}")
                    return False
            else:
                readme_url = url
            
            if verbose:
                print(f"Fetching from {readme_url}...")
            
            # Fetch content
            async with session.get(readme_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"✗ Failed to fetch (HTTP {resp.status})")
                    return False
                content = await resp.text()
            
            # Determine name
            if custom_name:
                name = custom_name
            else:
                # Extract from URL
                parsed = urlparse(url)
                if "github.com" in url:
                    parts = parsed.path.strip("/").split("/")
                    name = f"{parts[0]}_{parts[1]}" if len(parts) >= 2 else "readme"
                else:
                    name = parsed.path.split("/")[-1].replace(".md", "") or "readme"
            
            # Save
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{name}.md"
            
            readme_content = create_readme_content(name, content, "custom", url)
            output_file.write_text(readme_content, encoding="utf-8")
            
            print(f"✓ Saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False


async def _get_github_readme_url(session: aiohttp.ClientSession, repo_url: str) -> Optional[str]:
    """Convert GitHub repo URL to raw README URL."""
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
                    return url
        except Exception:
            continue
    return None

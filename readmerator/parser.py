"""Parse Python and npm dependency files."""

import re
import ast
import json
import configparser
from pathlib import Path
from typing import List, Set, Dict


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


def parse_pyproject_toml(file_path: Path) -> List[str]:
    """Parse pyproject.toml and extract package names."""
    packages: Set[str] = set()
    
    if not file_path.exists():
        return []
    
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return []
    
    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        
        # Check [project.dependencies]
        if "project" in data and "dependencies" in data["project"]:
            for dep in data["project"]["dependencies"]:
                match = re.match(r"^([a-zA-Z0-9_-]+)", dep.strip())
                if match:
                    packages.add(match.group(1).lower())
        
        # Check [tool.poetry.dependencies]
        if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
            for pkg in data["tool"]["poetry"]["dependencies"]:
                if pkg != "python":
                    packages.add(pkg.lower())
    except Exception:
        pass
    
    return sorted(packages)


def parse_setup_py(file_path: Path) -> List[str]:
    """Parse setup.py and extract package names."""
    if not file_path.exists():
        return []
    
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        packages = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setup":
                packages.update(_extract_setup_deps(node.keywords))
        
        return sorted(packages)
    except Exception:
        return []


def _extract_setup_deps(keywords) -> Set[str]:
    """Extract dependencies from setup() keywords."""
    packages = set()
    for kw in keywords:
        if kw.arg in ("install_requires", "requires") and isinstance(kw.value, ast.List):
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and (match := re.match(r"^([a-zA-Z0-9_-]+)", elt.value)):
                    packages.add(match.group(1).lower())
    return packages


def parse_setup_cfg(file_path: Path) -> List[str]:
    """Parse setup.cfg and extract package names."""
    packages: Set[str] = set()
    
    if not file_path.exists():
        return []
    
    try:
        config = configparser.ConfigParser()
        config.read(file_path)
        
        if "options" in config and "install_requires" in config["options"]:
            deps = config["options"]["install_requires"]
            for line in deps.splitlines():
                line = line.strip()
                if line:
                    match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                    if match:
                        packages.add(match.group(1).lower())
    except Exception:
        pass
    
    return sorted(packages)


def parse_pipfile(file_path: Path) -> List[str]:
    """Parse Pipfile and extract package names."""
    packages: Set[str] = set()
    
    if not file_path.exists():
        return []
    
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return []
    
    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        
        for section in ["packages", "dev-packages"]:
            if section in data:
                for pkg in data[section]:
                    packages.add(pkg.lower())
    except Exception:
        pass
    
    return sorted(packages)


def parse_environment_yml(file_path: Path) -> List[str]:
    """Parse environment.yml and extract pip package names."""
    packages: Set[str] = set()
    
    if not file_path.exists():
        return []
    
    try:
        content = file_path.read_text(encoding="utf-8")
        in_pip_section = False
        
        for line in content.splitlines():
            stripped = line.strip()
            
            if stripped.startswith("- pip:"):
                in_pip_section = True
                continue
            
            if in_pip_section:
                if stripped.startswith("-"):
                    if not stripped.startswith("- "):
                        in_pip_section = False
                        continue
                    
                    dep = stripped[2:].strip()
                    match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                    if match:
                        packages.add(match.group(1).lower())
                elif stripped and not stripped.startswith(" "):
                    in_pip_section = False
    except Exception:
        pass
    
    return sorted(packages)


def parse_package_json(file_path: Path) -> List[str]:
    """Parse package.json and extract npm package names."""
    if not file_path.exists():
        return []
    
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        packages = set()
        
        for section in ["dependencies", "devDependencies"]:
            if section in data:
                packages.update(data[section].keys())
        
        return sorted(packages)
    except Exception:
        return []


def find_and_parse_all_dependencies(directory: Path, recursive: bool = True, max_depth: int | None = None) -> Dict[str, List[str]]:
    """Find and parse all dependency files in directory.
    
    Args:
        directory: Root directory to search
        recursive: If True, scan subdirectories recursively
        max_depth: Maximum depth to recurse (None = unlimited)
    
    Returns:
        Dict with 'python' and 'npm' keys containing package lists
    """
    python_packages: Set[str] = set()
    npm_packages: Set[str] = set()
    exclude_dirs = {'.venv', 'venv', 'env', '.env', 'node_modules', '.git', '__pycache__', 'build', 'dist', '.tox', '.pytest_cache', '.mypy_cache', 'site-packages'}
    
    python_parsers = [
        ("requirements.txt", parse_requirements_txt),
        ("pyproject.toml", parse_pyproject_toml),
        ("setup.py", parse_setup_py),
        ("setup.cfg", parse_setup_cfg),
        ("Pipfile", parse_pipfile),
        ("environment.yml", parse_environment_yml),
    ]
    
    npm_parsers = [
        ("package.json", parse_package_json),
    ]
    
    def scan_directory(path: Path, depth: int = 0):
        if max_depth is not None and depth > max_depth:
            return
        
        for filename, parser in python_parsers:
            packages = parser(path / filename)
            if packages:
                python_packages.update(packages)
        
        for filename, parser in npm_parsers:
            packages = parser(path / filename)
            if packages:
                npm_packages.update(packages)
        
        if recursive:
            for item in path.iterdir():
                if item.is_dir() and item.name not in exclude_dirs:
                    scan_directory(item, depth + 1)
    
    scan_directory(directory)
    return {
        "python": sorted(python_packages),
        "npm": sorted(npm_packages)
    }


def find_dependency_file(directory: Path) -> Path | None:
    """Find requirements.txt in directory (legacy function)."""
    req_file = directory / "requirements.txt"
    if req_file.exists():
        return req_file
    return None

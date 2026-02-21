"""Parse Python dependency files."""

import re
import ast
import configparser
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
    packages: Set[str] = set()
    
    if not file_path.exists():
        return []
    
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "setup":
                    for keyword in node.keywords:
                        if keyword.arg in ("install_requires", "requires"):
                            if isinstance(keyword.value, ast.List):
                                for elt in keyword.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        match = re.match(r"^([a-zA-Z0-9_-]+)", elt.value)
                                        if match:
                                            packages.add(match.group(1).lower())
    except Exception:
        pass
    
    return sorted(packages)


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


def find_and_parse_all_dependencies(directory: Path) -> List[str]:
    """Find and parse all dependency files in directory."""
    all_packages: Set[str] = set()
    
    # Try all formats
    parsers = [
        ("requirements.txt", parse_requirements_txt),
        ("pyproject.toml", parse_pyproject_toml),
        ("setup.py", parse_setup_py),
        ("setup.cfg", parse_setup_cfg),
        ("Pipfile", parse_pipfile),
        ("environment.yml", parse_environment_yml),
    ]
    
    for filename, parser in parsers:
        file_path = directory / filename
        packages = parser(file_path)
        if packages:
            all_packages.update(packages)
    
    return sorted(all_packages)


def find_dependency_file(directory: Path) -> Path | None:
    """Find requirements.txt in directory (legacy function)."""
    req_file = directory / "requirements.txt"
    if req_file.exists():
        return req_file
    return None

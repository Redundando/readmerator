"""Command-line interface for readmerator."""

import asyncio
import argparse
from pathlib import Path
import sys

from .parser import parse_requirements_txt, find_dependency_file, find_and_parse_all_dependencies
from .fetcher import fetch_all_readmes, fetch_readme_from_url


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and cache README files for Python dependencies"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".ai-docs"),
        help="Output directory for README files (default: .ai-docs)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Path to requirements.txt (default: auto-detect)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only scan root directory, not subdirectories",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        help="Maximum directory depth to scan (default: unlimited)",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Fetch README from a specific URL (e.g., GitHub repo or raw README URL)",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Custom name for the README when using --url (default: extracted from URL)",
    )
    
    args = parser.parse_args()
    
    # Handle URL mode
    if args.url:
        success = asyncio.run(fetch_readme_from_url(args.url, args.output_dir, args.name, args.verbose))
        sys.exit(0 if success else 1)
    
    # Find dependency file
    if args.source:
        dep_file = args.source
        if not dep_file.exists():
            print(f"Error: {dep_file} not found", file=sys.stderr)
            sys.exit(1)
        packages = {"python": parse_requirements_txt(dep_file), "npm": []}
    else:
        # Parse all dependency files in directory
        packages = find_and_parse_all_dependencies(
            Path.cwd(),
            recursive=not args.no_recursive,
            max_depth=args.max_depth
        )
    
    total_packages = len(packages["python"]) + len(packages["npm"])
    if total_packages == 0:
        print("No packages found in dependency files")
        sys.exit(0)
    
    print(f"Found {total_packages} packages")
    if packages["python"]:
        print(f"  Python: {len(packages['python'])} packages")
    if packages["npm"]:
        print(f"  npm: {len(packages['npm'])} packages")
    print(f"Fetching READMEs to {args.output_dir}/")
    
    # Fetch READMEs
    results = asyncio.run(fetch_all_readmes(packages, args.output_dir, args.verbose))
    
    # Summary
    print()
    for ecosystem in ["python", "npm"]:
        if not results[ecosystem]:
            continue
        success_count = sum(1 for v in results[ecosystem].values() if v)
        fail_count = len(results[ecosystem]) - success_count
        
        print(f"{ecosystem.capitalize()}:")
        print(f"  ✓ Successfully fetched: {success_count}")
        if fail_count > 0:
            print(f"  ✗ Failed: {fail_count}")
            if not args.verbose:
                failed = [pkg for pkg, success in results[ecosystem].items() if not success]
                print(f"    Failed packages: {', '.join(failed)}")
    
    print(f"\nREADMEs saved to {args.output_dir}/")
    print(f"Use '@folder {args.output_dir}' in your AI assistant to include documentation")


if __name__ == "__main__":
    main()

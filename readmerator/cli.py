"""Command-line interface for readmerator."""

import asyncio
import argparse
from pathlib import Path
import sys

from .parser import parse_requirements_txt, find_dependency_file
from .fetcher import fetch_all_readmes


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
    
    args = parser.parse_args()
    
    # Find dependency file
    if args.source:
        dep_file = args.source
        if not dep_file.exists():
            print(f"Error: {dep_file} not found", file=sys.stderr)
            sys.exit(1)
    else:
        dep_file = find_dependency_file(Path.cwd())
        if not dep_file:
            print("Error: No requirements.txt found in current directory", file=sys.stderr)
            sys.exit(1)
    
    # Parse dependencies
    packages = parse_requirements_txt(dep_file)
    if not packages:
        print(f"No packages found in {dep_file}")
        sys.exit(0)
    
    print(f"Found {len(packages)} packages in {dep_file}")
    print(f"Fetching READMEs to {args.output_dir}/")
    
    # Fetch READMEs
    results = asyncio.run(fetch_all_readmes(packages, args.output_dir, args.verbose))
    
    # Summary
    success_count = sum(1 for v in results.values() if v)
    fail_count = len(results) - success_count
    
    print(f"\n✓ Successfully fetched: {success_count}")
    if fail_count > 0:
        print(f"✗ Failed: {fail_count}")
        if not args.verbose:
            failed = [pkg for pkg, success in results.items() if not success]
            print(f"  Failed packages: {', '.join(failed)}")
    
    print(f"\nREADMEs saved to {args.output_dir}/")
    print(f"Use '@folder {args.output_dir}' in your AI assistant to include documentation")


if __name__ == "__main__":
    main()

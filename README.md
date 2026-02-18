# readmerator

Fetch and cache README files for Python dependencies to use with AI coding assistants.

## Problem

When working with AI coding assistants (like Amazon Q, GitHub Copilot, etc.), they can't automatically access documentation for your imported packages. This means you have to manually look up package docs or copy-paste them into context.

## Solution

`readmerator` automatically fetches README files for all your project dependencies and saves them locally. You can then use your AI assistant's context features (like `@folder`) to include all documentation at once.

## Installation

```bash
pip install readmerator
```

## Usage

Run in your project directory:

```bash
readmerator
```

This will:
1. Find your `requirements.txt`
2. Fetch README files from PyPI and GitHub for each package
3. Save them to `.ai-docs/` directory

Then in your AI assistant, use:
```
@folder .ai-docs
```

Now the AI has access to all your dependency documentation!

## Options

```bash
readmerator --output-dir docs/packages  # Custom output directory
readmerator --source requirements.txt   # Specify requirements file
readmerator --verbose                   # Show detailed progress
```

## Example

```bash
$ readmerator
Found 15 packages in requirements.txt
Fetching READMEs to .ai-docs/

✓ Successfully fetched: 14
✗ Failed: 1
  Failed packages: some-private-package

READMEs saved to .ai-docs/
Use '@folder .ai-docs' in your AI assistant to include documentation
```

## Output Format

Each package gets a markdown file with metadata:

```markdown
---
Package: requests
Version: 2.31.0
Source: https://github.com/psf/requests
Fetched: 2024-01-15 10:30:00
---

[README content here...]
```

## Features

- ✓ Fetches from PyPI and GitHub
- ✓ Async/concurrent for speed
- ✓ Graceful error handling
- ✓ Progress indicators
- ✓ Minimal dependencies

## Requirements

- Python 3.8+
- aiohttp

## License

MIT

# Example Fullstack Project Structure

## Directory Layout

```
example-fullstack/
├── requirements.txt          # Python: flask, requests, sqlalchemy
├── package.json             # npm: react, react-dom, axios, vite, @types/react, eslint
├── backend/
│   ├── requirements.txt     # Python: pytest, black
│   └── app.py
├── frontend/
│   ├── package.json        # npm: lodash, prettier
│   └── App.jsx
└── README.md
```

## Running the Example

```bash
# Navigate to the example directory
cd example-fullstack

# Run readmerator (will auto-detect all dependency files recursively)
readmerator

# Or run from parent directory
cd ..
readmerator --source example-fullstack
```

## What Happens

1. **Auto-detection**: Scans root + subdirectories for:
   - `requirements.txt` files (Python)
   - `package.json` files (npm)

2. **Package Discovery**:
   - **Python**: 5 packages (flask, requests, sqlalchemy, pytest, black)
   - **npm**: 8 packages (react, react-dom, axios, vite, @types/react, eslint, lodash, prettier)
   - **Total**: 13 packages

3. **Fetching**:
   - Python packages from PyPI/GitHub
   - npm packages from npm registry

4. **Output Structure**:
```
.ai-docs/
├── python/
│   ├── flask.md
│   ├── requests.md
│   ├── sqlalchemy.md
│   ├── pytest.md
│   └── black.md
└── npm/
    ├── react.md
    ├── react-dom.md
    ├── axios.md
    ├── vite.md
    ├── types_react.md      # @types/react
    ├── eslint.md
    ├── lodash.md
    └── prettier.md
```

## Expected Console Output

```
Found 13 packages
  Python: 5 packages
  npm: 8 packages
Fetching READMEs to .ai-docs/

Fetching flask...
  ✓ flask: Saved (15234 bytes) from PyPI
Fetching requests...
  ✓ requests: Saved (18923 bytes) from GitHub
...

Python:
  ✓ Successfully fetched: 5
npm:
  ✓ Successfully fetched: 8

READMEs saved to .ai-docs/
Use '@folder .ai-docs' in your AI assistant to include documentation
```

## Using with AI Assistants

### Amazon Q
```
@folder .ai-docs
How do I use Flask with SQLAlchemy?
```

### GitHub Copilot
```
#file:.ai-docs/**/*
```

### Cursor
```
@Docs .ai-docs
```

## Testing Recursive Scanning

```bash
# Scan only root directory (no subdirectories)
readmerator --no-recursive
# Result: 9 packages (3 Python + 6 npm)

# Scan with depth limit
readmerator --max-depth 1
# Result: 13 packages (all of them)

# Scan all (default)
readmerator
# Result: 13 packages (all of them)
```

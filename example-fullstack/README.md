# Example Fullstack Project

This is a demo project showcasing **readmerator** with both Python and npm dependencies.

## Structure

- **Backend**: Flask API (Python)
- **Frontend**: React app (npm)

## Dependencies

### Python (Backend)
- `flask` - Web framework
- `requests` - HTTP library
- `sqlalchemy` - Database ORM

### npm (Frontend)
- `react` - UI library
- `react-dom` - React DOM renderer
- `axios` - HTTP client
- `vite` - Build tool (dev)
- `@types/react` - TypeScript types (dev)
- `eslint` - Linter (dev)

## Usage

Run readmerator in this directory:

```bash
cd example-fullstack
readmerator
```

This will:
1. Auto-detect both `requirements.txt` and `package.json`
2. Fetch READMEs for all 9 packages
3. Organize them into:
   - `.ai-docs/python/` - 3 Python packages
   - `.ai-docs/npm/` - 6 npm packages

Then reference in your AI assistant:
```
@folder .ai-docs
```

## Expected Output

```
Found 9 packages
  Python: 3 packages
  npm: 6 packages
Fetching READMEs to .ai-docs/

Python:
  ✓ Successfully fetched: 3
npm:
  ✓ Successfully fetched: 6

READMEs saved to .ai-docs/
Use '@folder .ai-docs' in your AI assistant to include documentation
```

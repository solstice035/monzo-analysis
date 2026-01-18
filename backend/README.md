# Monzo Analysis Backend

FastAPI backend for personal finance tracking and analytics using the Monzo API.

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run server
uvicorn app.main:app --reload
```

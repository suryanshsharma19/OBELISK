# OBELISK Backend

FastAPI backend for OBELISK supply chain security platform.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## Testing

```bash
pytest
```

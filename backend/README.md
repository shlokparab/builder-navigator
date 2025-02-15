# FastAPI Backend

This is a basic FastAPI backend with example endpoints.

## Setup

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

Start the server with:
```bash
uvicorn main:app --reload --port 8000
```

The server will run at `http://localhost:8000`

## Available Endpoints

- `GET /`: Returns a hello world message
- `GET /items/{item_id}`: Returns information about an item with the specified ID

## API Documentation

Once the server is running, you can view the automatic API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
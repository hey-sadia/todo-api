# Task API (CRUD)

A simple Task management API built with FastAPI, supporting full CRUD operations (Create, Read, Update, Delete) on an in-memory task list.

## How to Run

1. Install dependencies:
2. Start the server:
3. Open your browser at `http://127.0.0.1:8000`

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | API info |
| GET | /health | Health check |
| GET | /tasks | Get all tasks |
| GET | /tasks/{id} | Get one task |
| POST | /tasks | Create a new task |
| PUT | /tasks/{id} | Update a task |
| DELETE | /tasks/{id} | Delete a task |

## Example curl output
curl -i -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d "{"title": "Buy milk"}"

HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
## Swagger UI

Interactive API documentation is available at `http://127.0.0.1:8000/docs`

See the repository files for a screenshot of the working Swagger UI.

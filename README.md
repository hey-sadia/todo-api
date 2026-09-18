# Todo API

A simple CRUD API for managing tasks, built with FastAPI and SQLModel, backed by a SQLite database.

This is the Week 3 version of the project: the same API from Assignment 1 now persists its data to disk instead of storing it in an in-memory list.

## Why SQLite

SQLite was chosen because it requires no separate database server or installation, it's just a single file on disk. That makes it perfect for learning how an API talks to a real database without extra setup. The same ideas (SQL queries, tables, rows) carry over directly if the project is later migrated to a bigger database like PostgreSQL.

## Where the database file is stored

The database lives in a single file, tasks.db, created automatically in the project's root folder the first time the app runs. It is not pushed to GitHub (see .gitignore).

## How to start the project

1. Install dependencies:
   pip install -r requirements.txt

2. Run the server:
   uvicorn main:app --reload

3. Open your browser at http://127.0.0.1:8000/docs

On the first run, tasks.db and the tasks table are created automatically, and three example tasks are inserted. Restarting the server afterwards will not duplicate them or erase data, everything is stored on disk now.

## API Endpoints

| Method | Endpoint      | Description                |
|--------|---------------|-----------------------------|
| GET    | /tasks        | List all tasks              |
| GET    | /tasks/{id}   | Get a single task           |
| POST   | /tasks        | Create a new task           |
| PUT    | /tasks/{id}   | Update a task               |
| DELETE | /tasks/{id}   | Delete a task                |
| GET    | /stats        | Task statistics (extra)     |

### Optional query parameters on GET /tasks

- ?search=milk : search tasks by title
- ?done=true : filter by completion status
- ?sort=title : sort tasks alphabetically

## Example SQL query

SELECT * FROM task WHERE done = 1;

This returns every completed task, and the API's GET /tasks?done=true endpoint returns exactly the same rows.

## Screenshot of the database viewer

![Database screenshot](screenshot.png)

## What changed from Assignment 1

- The API's URLs, request bodies, and response shapes are unchanged.
- Only the storage layer changed: an in-memory list became a SQLite table accessed through SQLModel.
- Data now survives server restarts.
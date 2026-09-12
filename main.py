from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def home():
    return {"name": "Task API", "version": "1.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Clean room", "done": False},
    {"id": 3, "title": "Read book", "done": True}
]

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.post("/tasks", status_code=201)
def create_task(task: dict):
    title = task.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    new_id = max([t["id"] for t in tasks], default=0) + 1
    new_task = {"id": new_id, "title": title, "done": False}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{id}")
def update_task(id: int, updates: dict):
    for task in tasks:
        if task["id"] == id:
            title = updates.get("title")
            if title is not None and not title:
                raise HTTPException(status_code=400, detail="Title cannot be empty")
            if title is not None:
                task["title"] = title
            if "done" in updates:
                task["done"] = updates["done"]
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from sqlmodel import SQLModel, Field, Session, create_engine, select, func

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tasks.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(SQLModel):
    title: Optional[str] = None
    done: bool = False


class TaskUpdate(SQLModel):
    title: Optional[str] = None
    done: Optional[bool] = None


app = FastAPI(title="Todo API")


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        existing = session.exec(select(Task)).first()
        if existing is None:
            example_tasks = [
                Task(title="Buy milk", done=False),
                Task(title="Read chapter 3", done=False),
                Task(title="Walk the dog", done=True),
            ]
            session.add_all(example_tasks)
            session.commit()


@app.get("/tasks")
def get_tasks(
    search: Optional[str] = Query(default=None),
    done: Optional[bool] = Query(default=None),
    sort: Optional[str] = Query(default=None),
):
    with Session(engine) as session:
        statement = select(Task)

        if search is not None:
            statement = statement.where(Task.title.like(f"%{search}%"))

        if done is not None:
            statement = statement.where(Task.done == done)

        if sort == "title":
            statement = statement.order_by(Task.title)

        tasks = session.exec(statement).all()
        return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task


@app.post("/tasks", status_code=201)
def create_task(task_in: TaskCreate):
    if not task_in.title or not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    with Session(engine) as session:
        task = Task(title=task_in.title.strip(), done=task_in.done)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_in: TaskUpdate):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        if task_in.title is not None:
            if not task_in.title.strip():
                raise HTTPException(status_code=400, detail="Title cannot be empty")
            task.title = task_in.title.strip()

        if task_in.done is not None:
            task.done = task_in.done

        task.updated_at = datetime.utcnow()

        session.add(task)
        session.commit()
        session.refresh(task)
        return task


@app.delete("/tasks/{task_id}", status_code=200)
def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        session.delete(task)
        session.commit()
        return {"message": "Task deleted"}


@app.get("/stats")
def get_stats():
    with Session(engine) as session:
        total = session.exec(select(func.count(Task.id))).one()
        completed = session.exec(
            select(func.count(Task.id)).where(Task.done == True)
        ).one()
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": total - completed,
        }
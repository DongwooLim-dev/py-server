import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("TASKS_DB", ROOT / "data" / "tasks.sqlite3"))


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    with database() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
    yield


app = FastAPI(title="Task API", lifespan=lifespan)


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("할 일 내용을 입력해 주세요.")
        return value


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    done: bool


def task_dict(row: sqlite3.Row) -> dict:
    task = dict(row)
    task["done"] = bool(task["done"])
    return task


@app.get("/health")
def health() -> dict[str, str]:
    with database() as db:
        db.execute("SELECT 1").fetchone()
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> list[dict]:
    with database() as db:
        rows = db.execute(
            "SELECT id, title, done, created_at FROM tasks ORDER BY id DESC"
        ).fetchall()
    return [task_dict(row) for row in rows]


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate) -> dict:
    with database() as db:
        cursor = db.execute(
            "INSERT INTO tasks (title, created_at) VALUES (?, ?)",
            (task.title, datetime.now(timezone.utc).isoformat()),
        )
        row = db.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return task_dict(row)


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate) -> dict:
    with database() as db:
        cursor = db.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (int(update.done), task_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")
        row = db.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return task_dict(row)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    with database() as db:
        cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다.")

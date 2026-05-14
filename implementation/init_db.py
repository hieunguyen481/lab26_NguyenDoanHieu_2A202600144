from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "sqlite_lab.db"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cohort TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0)
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0)
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 100),
    semester TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    UNIQUE (student_id, course_id, semester)
);
"""


STUDENTS = [
    ("An Nguyen", "an.nguyen@example.edu", "A1", 20),
    ("Binh Tran", "binh.tran@example.edu", "A1", 21),
    ("Chi Le", "chi.le@example.edu", "A2", 19),
    ("Dung Pham", "dung.pham@example.edu", "A2", 22),
    ("Minh Hoang", "minh.hoang@example.edu", "A3", 20),
]

COURSES = [
    ("MCP101", "Model Context Protocol Basics", 3),
    ("DB201", "Applied Databases", 4),
    ("AI305", "AI Tool Integration", 3),
]

ENROLLMENTS = [
    (1, 1, 88.5, "2026S"),
    (1, 2, 91.0, "2026S"),
    (2, 1, 79.0, "2026S"),
    (2, 3, 84.5, "2026S"),
    (3, 2, 93.0, "2026S"),
    (3, 3, 89.5, "2026S"),
    (4, 1, 72.0, "2026S"),
    (5, 3, 95.0, "2026S"),
]


def create_database(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.executemany(
            "INSERT INTO students (name, email, cohort, age) VALUES (?, ?, ?, ?)",
            STUDENTS,
        )
        conn.executemany(
            "INSERT INTO courses (code, title, credits) VALUES (?, ?, ?)",
            COURSES,
        )
        conn.executemany(
            """
            INSERT INTO enrollments (student_id, course_id, score, semester)
            VALUES (?, ?, ?, ?)
            """,
            ENROLLMENTS,
        )
        conn.commit()

    return path


if __name__ == "__main__":
    database_path = create_database()
    print(f"Created SQLite database at {database_path}")

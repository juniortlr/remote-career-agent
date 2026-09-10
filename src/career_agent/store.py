import json
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from .models import Job


def canonical_url(url):
    parsed = urlsplit(url)
    # Preserve query parameters: some ATS systems put the job ID in the query.
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), parsed.query, ""))


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, url TEXT UNIQUE NOT NULL, data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT NOT NULL,
            package TEXT NOT NULL
        );
        """)
        self.db.execute("PRAGMA foreign_keys=ON")

    def close(self):
        self.db.close()

    def add(self, job: Job):
        url = canonical_url(job.url)
        existing = self.db.execute("SELECT id FROM jobs WHERE id=? OR url=?", (job.key, url)).fetchone()
        if existing:
            return existing["id"]
        with self.db:
            self.db.execute("INSERT INTO jobs VALUES(?,?,?)", (job.key, url, json.dumps(job.to_dict())))
        return job.key

    def jobs(self):
        return [Job(**json.loads(row[0])) for row in self.db.execute("SELECT data FROM jobs ORDER BY rowid DESC")]

    def get(self, key):
        row = self.db.execute("SELECT data FROM jobs WHERE id=?", (key,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown job: {key}")
        return Job(**json.loads(row[0]))

    def save_draft(self, job_id, package):
        with self.db:
            cur = self.db.execute("INSERT INTO applications(job_id,status,package) VALUES(?,?,?)",
                                  (job_id, "draft", json.dumps(package)))
        return cur.lastrowid

    def applications(self):
        return [dict(row) | {"package": json.loads(row["package"])} for row in
                self.db.execute("SELECT * FROM applications ORDER BY id DESC")]

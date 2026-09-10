"""Optional read-only local API. Install the api extra to run."""
import os
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .models import evaluate
from .store import Store

app = FastAPI(title="Remote Career Agent", version="0.1.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]"])


@app.get("/health")
def health():
    return {"status": "ok", "submission_enabled": False}


@app.get("/jobs")
def jobs():
    store = Store(os.environ.get("CAREER_DB", "var/career.sqlite3"))
    try:
        return [job.to_dict() | {"id": job.key, "evaluation": evaluate(job)} for job in store.jobs()]
    finally:
        store.close()


@app.get("/applications")
def applications():
    store = Store(os.environ.get("CAREER_DB", "var/career.sqlite3"))
    try:
        return store.applications()
    finally:
        store.close()

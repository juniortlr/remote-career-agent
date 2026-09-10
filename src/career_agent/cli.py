import argparse
import json
from pathlib import Path
from .models import Job, evaluate
from .sources import discover
from .store import Store
from .tailoring import prepare


def main():
    parser = argparse.ArgumentParser(description="Local remote-job application preparation")
    parser.add_argument("--db", default="var/career.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    load = commands.add_parser("import-job")
    load.add_argument("file")
    scan = commands.add_parser("discover")
    scan.add_argument("source", choices=["wwr", "greenhouse", "lever"])
    scan.add_argument("--board")
    commands.add_parser("jobs")
    commands.add_parser("applications")
    draft = commands.add_parser("draft")
    draft.add_argument("job_id")
    draft.add_argument("--profile", required=True)
    args = parser.parse_args()
    store = Store(args.db)
    try:
        if args.command == "init":
            result = {"database": args.db, "status": "ready"}
        elif args.command == "import-job":
            result = {"job_id": store.add(Job(**json.loads(Path(args.file).read_text(encoding="utf-8"))))}
        elif args.command == "discover":
            result = {"job_ids": [store.add(job) for job in discover(args.source, args.board)]}
        elif args.command == "jobs":
            result = [{"id": job.key, "title": job.title, "company": job.company, **evaluate(job)} for job in store.jobs()]
        elif args.command == "applications":
            result = store.applications()
        else:
            profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
            package = prepare(store.get(args.job_id), profile)
            result = {"application_id": store.save_draft(args.job_id, package), **package}
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    finally:
        store.close()


if __name__ == "__main__":
    main()

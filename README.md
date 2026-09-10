# Remote Career Agent

A Python scaffold for finding remote AI Engineering, Data Science and Data Engineering jobs and preparing applications from verified career evidence. Designed to run on your home desktop.

**Status: working discovery/preparation CLI, not an autonomous applicant.** The LLM writer, resume file export, dashboard, scheduler and browser submission are planned extension points. No application is sent by this release.

## Quick start (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
career-agent init
career-agent import-job examples/job.json
career-agent draft manual:demo-data-engineer --profile examples/profile.json
career-agent jobs
career-agent applications
```

Use any installed Python 3.11+; on macOS/Linux use `python3 -m venv .venv` and `source .venv/bin/activate`. If PowerShell activation is unavailable, run `.venv\Scripts\python.exe -m career_agent.cli` in place of `career-agent`.

The examples are fictional. Copy examples/profile.json to **profile.private.json** and enter your actual evidence. Only items explicitly marked `verified: true` are eligible for drafting. Keep real profile data and output under ignored paths.

## Discover jobs

```powershell
career-agent discover wwr
career-agent discover greenhouse --board YOUR_COMPANY_BOARD
career-agent discover lever --board YOUR_COMPANY_BOARD
```

Greenhouse and Lever need a known company board slug; these are not global search APIs. Sources are read-only. WWR job URLs preserve attribution to [We Work Remotely](https://weworkremotely.com/remote-job-rss-feed). Network calls have a timeout and response-size cap. Source restrictions and network outages are reported as errors.

Discovery intentionally leaves eligibility/payment fields unknown instead of guessing. Remote does not mean eligible in Brazil; USD salary display does not prove USD payment. A job qualifies only with confirmed remote/Brazil/USD flags, monthly USD compensation >= 4500, and salary/eligibility evidence. Manually import a completed job record for this initial version. Reimporting the same key or URL preserves the first record; editing and refresh are pending.

## Tailoring baseline

Verified career evidence is ranked by overlap with the specific job and questions. Relevant bullet text and evidence IDs are saved verbatim. Exact approved answers can be reused but remain review-required; all other questions are left unanswered with suggested evidence. This is an auditable baseline for a future LLM writer, not semantic matching or polished answer generation.

## Optional local API

```powershell
python -m pip install -e ".[api]"
python -m uvicorn career_agent.api:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765/docs for read-only endpoints. Never expose this unauthenticated service to the network. Database defaults to var/career.sqlite3; CLI supports `--db PATH` before the subcommand, API supports CAREER_DB.

## Tests

```powershell
python -m unittest discover -s tests -v
```

CI runs core tests on Windows/Linux with Python 3.11/3.12. Tests are offline and never submit applications. Optional API dependencies are not part of core tests.

## Publish to your GitHub account

With GitHub CLI installed and authenticated, from the extracted project directory:

```powershell
git init -b main
git add .
git commit -m "Scaffold local remote career agent"
gh repo create remote-career-agent --private --source . --remote origin --push
```

If using an existing empty repository instead, set its URL with `git remote add origin URL` then `git push -u origin main`. Do not commit private profile data.

See [architecture and roadmap](docs/architecture.md) for implementation boundaries and next steps.

# Architecture and implementation plan

## Implemented

CLI -> read-only source adapters -> normalized Job -> SQLite -> eligibility checks -> evidence selection -> stored draft.

Core is standard-library Python 3.11+. Optional FastAPI exposes read-only job and application lists for a future desktop UI. SQLite persists drafts and snapshots across restarts. No worker or scheduler is running yet.

Sources: WWR RSS, Greenhouse company boards, Lever company boards. Wellfound applications are manual initially; the app can store user-authored job notes through import-job. No Wellfound scraper is provided.

Data: jobs have source IDs and unique canonical URLs. Applications store immutable draft packages, including the profile snapshot and generator version. Reimporting a known job returns the existing record; refresh/merge UI remains pending. Cross-board fuzzy deduplication is pending.

## Next milestones

1. Profile editor and job detail editor: verify evidence, update imported compensation and Brazil eligibility, configure role filters and salary floor. Current floor is USD 4,500 monthly; core evaluate accepts an override.
2. Provider interface and structured LLM generation: separate job text from system instructions; select only verified evidence; enforce word limits, return evidence IDs and unsupported-claim warnings; require review. Exact approved answers currently reuse verbatim and always require review.
3. DOCX/PDF generation, accessible local dashboard and draft review. Candidate private data must never ship in fixtures.
4. Persistent worker queue with leases, cancellation, bounded retries, wake/resume behavior, per-source rate limits and run history. Initial discovery is synchronous and manually triggered.
5. One Playwright adapter after verifying platform rules. Separate browser session, user login/MFA/CAPTCHA handoff, exact package approval, confirmation capture.
6. Automatic mode only after confirmed submission works. Bind approvals to package hashes and policy version. Use a unique application intent per canonical job. On crash after submission begins, enter submission_uncertain and reconcile; never blindly resubmit.
7. Interview/outcome tracking and conversion by source/role. No automated recruiter messaging in the initial release.

## Proposed submission states (not implemented)

draft -> needs_review -> approved -> submitting -> submitted
submitting -> submission_uncertain -> manual reconciliation
needs_review -> rejected

## Security

Loopback API, no CORS wildcard, trusted Host allowlist. API currently read-only; add CSRF protection and local authentication before browser mutations. Use OS credential storage for future provider keys. No arbitrary URL fetching: source endpoints are fixed, board slugs validated. Do not log secrets or send entire profiles to an LLM by default. Keep user documents under ignored var/. Cloud LLM use will need an explicit configurable data-sharing setting.

## Sources checked during planning

- https://weworkremotely.com/remote-job-rss-feed (retain attribution)
- https://wellfound.com/terms
- https://docs.greenhouse.io/job-board.html
- https://github.com/lever/postings-api

Public discovery and employer-authenticated submission are separate capabilities. Recheck platform policies before introducing browser submission.

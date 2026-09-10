"""Deterministic, evidence-only baseline. No fabricated answers or LLM calls."""
import re
from .models import evaluate


def tokens(text):
    return set(re.findall(r"[a-z0-9+#]+", text.lower()))


def prepare(job, profile):
    facts = profile.get("evidence", [])
    if len({item["id"] for item in facts}) != len(facts):
        raise ValueError("Evidence IDs must be unique")
    verified = [item for item in facts if item.get("verified") is True]
    def rank(text):
        query = tokens(text)
        scored = [(len(query & tokens(item["text"] + " " + " ".join(item.get("tags", [])))), item) for item in verified]
        return [item for score, item in sorted(scored, key=lambda pair: (-pair[0], pair[1]["id"])) if score > 0][:4]
    selected = rank(job.title + " " + job.description)
    answers = []
    approved = profile.get("approved_answers", {})
    for question in job.questions:
        # Only exact, explicitly approved responses can be reused automatically.
        answer = approved.get(question)
        answers.append({"question": question, "answer": answer,
                        "status": "review" if answer else "needs_clarification",
                        "supporting_evidence": [item["id"] for item in rank(question)]})
    return {"job_id": job.key, "company": job.company, "title": job.title, "url": job.url,
            "generator": "evidence-baseline-v1", "status": "draft", "eligibility": evaluate(job),
            "resume_bullets": [{"text": item["text"], "evidence_id": item["id"]} for item in selected],
            "answers": answers, "profile_snapshot": profile,
            "limitations": ["Resume bullets are selected verbatim; prose rewriting and document export are not implemented.",
                            "No application has been submitted."]}

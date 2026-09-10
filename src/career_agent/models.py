from dataclasses import asdict, dataclass, field
from urllib.parse import urlsplit
import re


def public_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("A public HTTPS job URL without credentials is required")
    return value


@dataclass
class Job:
    source: str
    external_id: str
    title: str
    company: str
    url: str
    description: str
    location: str = ""
    remote: bool | None = None
    brazil_eligible: bool | None = None
    monthly_usd: float | None = None
    paid_in_usd: bool | None = None
    salary_evidence: str = ""
    eligibility_evidence: str = ""
    questions: list[str] = field(default_factory=list)

    def __post_init__(self):
        public_url(self.url)
        for key in ("source", "external_id", "title", "company", "description"):
            if not isinstance(getattr(self, key), str) or not getattr(self, key).strip():
                raise ValueError(f"{key} must be a nonempty string")
        for key in ("remote", "brazil_eligible", "paid_in_usd"):
            if getattr(self, key) is not None and type(getattr(self, key)) is not bool:
                raise ValueError(f"{key} must be true, false or null")
        if self.monthly_usd is not None:
            import math
            if type(self.monthly_usd) not in (int, float) or not math.isfinite(self.monthly_usd) or self.monthly_usd < 0:
                raise ValueError("monthly_usd must be a finite nonnegative number")
        if not isinstance(self.questions, list) or any(not isinstance(q, str) for q in self.questions):
            raise ValueError("questions must be a list of strings")

    @property
    def key(self):
        return f"{self.source}:{self.external_id}"

    def to_dict(self):
        return asdict(self)


def evaluate(job: Job, minimum_usd: float = 4500) -> dict:
    reasons, unknown = [], []
    role = re.search(r"(ai|artificial intelligence|ml|machine learning|data) (engineer|scientist|science|engineering)", job.title.lower())
    if not role:
        reasons.append("Title outside configured AI/ML/data role families")
    for name in ("remote", "brazil_eligible", "paid_in_usd"):
        value = getattr(job, name)
        if value is False:
            reasons.append(f"{name} is false")
        elif value is None:
            unknown.append(name)
    if job.monthly_usd is None:
        unknown.append("monthly_usd")
    elif job.monthly_usd < minimum_usd:
        reasons.append("Compensation below monthly USD floor")
    if not job.salary_evidence:
        unknown.append("salary_evidence")
    if not job.eligibility_evidence:
        unknown.append("eligibility_evidence")
    return {"decision": "excluded" if reasons else "needs_clarification" if unknown else "qualified",
            "reasons": reasons, "unknown": unknown}

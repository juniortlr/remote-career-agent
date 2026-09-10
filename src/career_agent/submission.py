"""Submission boundary reserved for future platform-specific adapters."""
from typing import Protocol


class SubmissionAdapter(Protocol):
    def submit(self, package: dict) -> dict:
        """Return confirmation evidence; never infer success from a click alone."""
        ...


class DisabledSubmission:
    def submit(self, package: dict) -> dict:
        raise NotImplementedError("Live submission is not implemented in this scaffold")

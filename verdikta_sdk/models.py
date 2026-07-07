"""Data models returned by the Verdikta Bounties API."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Job:
    """A bounty/job listing."""

    id: str
    title: str
    description: str
    status: str
    bounty_usd: Optional[float] = None
    hours_left: Optional[float] = None
    work_product_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create a Job from an API response dict."""
        return cls(
            id=str(data.get("id", data.get("_id", ""))),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", ""),
            bounty_usd=data.get("bountyUSD", data.get("bounty_usd")),
            hours_left=data.get("hoursLeft", data.get("hours_left")),
            work_product_type=data.get("workProductType", data.get("work_product_type")),
            created_at=_parse_dt(data.get("createdAt", data.get("created_at"))),
            updated_at=_parse_dt(data.get("updatedAt", data.get("updated_at"))),
            raw=data,
        )


@dataclass
class Submission:
    """A submission to a job."""

    id: str
    job_id: str
    status: str
    submitted_at: Optional[datetime] = None
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], job_id: str = "") -> "Submission":
        return cls(
            id=str(data.get("id", data.get("_id", ""))),
            job_id=job_id or str(data.get("jobId", data.get("job_id", ""))),
            status=data.get("status", ""),
            submitted_at=_parse_dt(data.get("submittedAt", data.get("submitted_at"))),
            raw=data,
        )


@dataclass
class Evaluation:
    """Evaluation results for a submission."""

    id: str
    submission_id: str
    score: Optional[float] = None
    passed: Optional[bool] = None
    feedback: Optional[str] = None
    criteria: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], submission_id: str = "") -> "Evaluation":
        return cls(
            id=str(data.get("id", data.get("_id", ""))),
            submission_id=submission_id or str(data.get("submissionId", data.get("submission_id", ""))),
            score=data.get("score"),
            passed=data.get("passed"),
            feedback=data.get("feedback"),
            criteria=data.get("criteria", []),
            raw=data,
        )


@dataclass
class Rubric:
    """Rubric/criteria for a job."""

    job_id: str
    criteria: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], job_id: str = "") -> "Rubric":
        return cls(
            job_id=job_id,
            criteria=data.get("criteria", []),
            raw=data,
        )


def _parse_dt(value: Any) -> Optional[datetime]:
    """Best-effort ISO datetime parse."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Python 3.7+: handle Z suffix
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None

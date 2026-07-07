"""Verdikta Bounties API SDK."""

from .client import VerdiktaClient
from .exceptions import (
    AuthError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    VerdiktaAPIError,
    VerdiktaError,
)
from .models import Evaluation, Job, Rubric, Submission

__all__ = [
    "VerdiktaClient",
    "Job",
    "Submission",
    "Evaluation",
    "Rubric",
    "VerdiktaError",
    "VerdiktaAPIError",
    "AuthError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "NetworkError",
]

__version__ = "0.1.0"

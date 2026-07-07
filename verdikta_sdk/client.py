"""HTTP client for the Verdikta Bounties API."""

import os
from typing import Any, BinaryIO, Dict, List, Optional, Union

import requests

from .exceptions import (
    AuthError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    VerdiktaAPIError,
)
from .models import Evaluation, Job, Rubric, Submission

_BASE_URL = "https://bounties.verdikta.org/api"


class VerdiktaClient:
    """Client for interacting with the Verdikta Bounties API.

    Args:
        api_key: API key for authentication. Falls back to the
            ``VERDIKTA_API_KEY`` environment variable if not provided.
        base_url: Override the API base URL (useful for testing).

    Raises:
        ValueError: If no API key is provided or found in the environment.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = _BASE_URL,
    ) -> None:
        key = api_key or os.environ.get("VERDIKTA_API_KEY")
        if not key:
            raise ValueError(
                "API key required. Pass api_key= or set VERDIKTA_API_KEY env var."
            )
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"X-Bot-API-Key": key})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_jobs(
        self,
        *,
        status: Optional[str] = None,
        work_product_type: Optional[str] = None,
        min_hours_left: Optional[float] = None,
        max_hours_left: Optional[float] = None,
        min_bounty_usd: Optional[float] = None,
        max_bounty_usd: Optional[float] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Job]:
        """List bounties with optional filters.

        Returns:
            A list of :class:`Job` objects matching the filters.
        """
        params: Dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if work_product_type is not None:
            params["workProductType"] = work_product_type
        if min_hours_left is not None:
            params["minHoursLeft"] = min_hours_left
        if max_hours_left is not None:
            params["maxHoursLeft"] = max_hours_left
        if min_bounty_usd is not None:
            params["minBountyUSD"] = min_bounty_usd
        if max_bounty_usd is not None:
            params["maxBountyUSD"] = max_bounty_usd
        if search is not None:
            params["search"] = search
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        data = self._get("/jobs", params=params)
        items = _extract_list(data)
        return [Job.from_dict(item) for item in items]

    def get_job(self, job_id: str) -> Job:
        """Get full details for a single bounty.

        Args:
            job_id: The bounty ID.

        Returns:
            A :class:`Job` object.

        Raises:
            NotFoundError: If the job does not exist.
        """
        data = self._get(f"/jobs/{job_id}")
        return Job.from_dict(_unwrap(data))

    def get_rubric(self, job_id: str) -> Rubric:
        """Get the evaluation rubric for a bounty.

        Args:
            job_id: The bounty ID.

        Returns:
            A :class:`Rubric` object.
        """
        data = self._get(f"/jobs/{job_id}/rubric")
        return Rubric.from_dict(_unwrap(data), job_id=job_id)

    def dry_run_submit(
        self,
        job_id: str,
        files: List[Union[str, BinaryIO]],
        *,
        filenames: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate a submission without actually submitting.

        Args:
            job_id: The bounty ID.
            files: List of file paths or file-like objects.
            filenames: Optional explicit filenames for the uploaded files.

        Returns:
            The API response dict with validation details.
        """
        multipart = self._build_multipart(files, filenames)
        return self._post(f"/jobs/{job_id}/submit/dry-run", files=multipart)

    def submit(
        self,
        job_id: str,
        files: List[Union[str, BinaryIO]],
        *,
        filenames: Optional[List[str]] = None,
    ) -> Submission:
        """Submit files to a bounty.

        Args:
            job_id: The bounty ID.
            files: List of file paths or file-like objects.
            filenames: Optional explicit filenames for the uploaded files.

        Returns:
            A :class:`Submission` object.
        """
        multipart = self._build_multipart(files, filenames)
        data = self._post(f"/jobs/{job_id}/submit", files=multipart)
        return Submission.from_dict(_unwrap(data), job_id=job_id)

    def submit_bundle(
        self,
        job_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit a full submission bundle (JSON payload).

        Args:
            job_id: The bounty ID.
            payload: The bundle payload to send.

        Returns:
            The API response dict.
        """
        return self._post(f"/jobs/{job_id}/submit/bundle", json_data=payload)

    def list_submissions(self, job_id: str) -> List[Submission]:
        """List all submissions for a bounty.

        Args:
            job_id: The bounty ID.

        Returns:
            A list of :class:`Submission` objects.
        """
        data = self._get(f"/jobs/{job_id}/submissions")
        items = _extract_list(data)
        return [Submission.from_dict(item, job_id=job_id) for item in items]

    def get_evaluation(self, job_id: str, submission_id: str) -> Evaluation:
        """Get evaluation results for a submission.

        Args:
            job_id: The bounty ID.
            submission_id: The submission ID.

        Returns:
            An :class:`Evaluation` object.
        """
        data = self._get(f"/jobs/{job_id}/submissions/{submission_id}/evaluation")
        return Evaluation.from_dict(_unwrap(data), submission_id=submission_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a GET request and return parsed JSON."""
        url = f"{self._base_url}{path}"
        try:
            resp = self._session.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            raise NetworkError(f"Request failed: {exc}") from exc
        self._check_status(resp)
        return resp.json()

    def _post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[list] = None,
    ) -> Any:
        """Execute a POST request and return parsed JSON."""
        url = f"{self._base_url}{path}"
        try:
            resp = self._session.post(url, json=json_data, files=files, timeout=60)
        except requests.RequestException as exc:
            raise NetworkError(f"Request failed: {exc}") from exc
        self._check_status(resp)
        return resp.json()

    @staticmethod
    def _check_status(resp: requests.Response) -> None:
        """Raise the appropriate exception for non-2xx responses."""
        if resp.ok:
            return
        try:
            body = resp.text
        except Exception:
            body = ""
        msg = _extract_error_message(body, resp.status_code)
        code = resp.status_code
        if code == 401 or code == 403:
            raise AuthError(msg, code)
        if code == 404:
            raise NotFoundError(msg, code)
        if code == 422:
            raise ValidationError(msg, code)
        if code == 429:
            raise RateLimitError(msg, code)
        raise VerdiktaAPIError(msg, code, body)

    @staticmethod
    def _build_multipart(
        files: List[Union[str, BinaryIO]],
        filenames: Optional[List[str]] = None,
    ) -> list:
        """Build a multipart files list for ``requests``.

        Returns a list of ``(field_name, (filename, fileobj))`` tuples
        compatible with the ``requests`` ``files`` parameter.
        """
        parts: list = []
        for i, f in enumerate(files):
            name = filenames[i] if filenames and i < len(filenames) else None
            if isinstance(f, str):
                fname = name or os.path.basename(f)
                parts.append(("files", (fname, open(f, "rb"))))
            else:
                fname = name or getattr(f, "name", f"file{i}")
                parts.append(("files", (fname, f)))
        return parts


# ------------------------------------------------------------------
# Response parsing helpers
# ------------------------------------------------------------------

def _extract_list(data: Any) -> List[Dict[str, Any]]:
    """Normalise the API response into a list of dicts."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Common wrappers: { "jobs": [...] }, { "data": [...] }, { "results": [...] }
        for key in ("jobs", "data", "results", "items", "submissions"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # If it's a single object, wrap it
        return [data]
    return []


def _unwrap(data: Any) -> Dict[str, Any]:
    """Unwrap a single-object response from a potential wrapper dict."""
    if isinstance(data, dict):
        for key in ("job", "data", "result", "rubric", "evaluation", "submission"):
            if key in data and isinstance(data[key], dict):
                return data[key]
        return data
    return {}


def _extract_error_message(body: str, status_code: int) -> str:
    """Try to pull an error message from the response body."""
    import json

    try:
        obj = json.loads(body)
        if isinstance(obj, dict):
            return obj.get("error", obj.get("message", body))
    except (json.JSONDecodeError, ValueError):
        pass
    return body or f"HTTP {status_code}"

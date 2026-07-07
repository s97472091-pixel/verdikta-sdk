"""Tests for the VerdiktaClient using mocked HTTP responses."""

import os

import pytest
import responses

from verdikta_sdk import (
    AuthError,
    Evaluation,
    Job,
    NetworkError,
    NotFoundError,
    Rubric,
    Submission,
    VerdiktaAPIError,
    VerdiktaClient,
)

BASE = "https://bounties.verdikta.org/api"


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Ensure a default API key is available."""
    monkeypatch.setenv("VERDIKTA_API_KEY", "test-key")


@pytest.fixture
def client():
    return VerdiktaClient()


# ------------------------------------------------------------------
# Constructor tests
# ------------------------------------------------------------------

class TestInit:
    def test_uses_env_var(self, monkeypatch):
        monkeypatch.setenv("VERDIKTA_API_KEY", "env-key")
        c = VerdiktaClient()
        assert c._session.headers["X-Bot-API-Key"] == "env-key"

    def test_uses_constructor_arg(self, monkeypatch):
        monkeypatch.delenv("VERDIKTA_API_KEY", raising=False)
        c = VerdiktaClient(api_key="arg-key")
        assert c._session.headers["X-Bot-API-Key"] == "arg-key"

    def test_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("VERDIKTA_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key required"):
            VerdiktaClient()


# ------------------------------------------------------------------
# list_jobs
# ------------------------------------------------------------------

class TestListJobs:
    @responses.activate
    def test_basic(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/jobs",
            json=[{"id": "1", "title": "Test", "description": "Desc", "status": "open"}],
            status=200,
        )
        jobs = client.list_jobs()
        assert len(jobs) == 1
        assert isinstance(jobs[0], Job)
        assert jobs[0].id == "1"
        assert jobs[0].title == "Test"

    @responses.activate
    def test_with_filters(self, client):
        responses.add(responses.GET, f"{BASE}/jobs", json=[], status=200)
        client.list_jobs(status="open", min_bounty_usd=100, limit=5)
        qs = responses.calls[0].request.url
        assert "status=open" in qs
        assert "minBountyUSD=100" in qs
        assert "limit=5" in qs

    @responses.activate
    def test_wrapped_response(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/jobs",
            json={"jobs": [{"id": "1", "title": "T", "description": "D", "status": "open"}]},
            status=200,
        )
        jobs = client.list_jobs()
        assert len(jobs) == 1


# ------------------------------------------------------------------
# get_job
# ------------------------------------------------------------------

class TestGetJob:
    @responses.activate
    def test_success(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/jobs/abc",
            json={"id": "abc", "title": "My Job", "description": "Desc", "status": "open", "bountyUSD": 500},
            status=200,
        )
        job = client.get_job("abc")
        assert isinstance(job, Job)
        assert job.id == "abc"
        assert job.bounty_usd == 500

    @responses.activate
    def test_not_found(self, client):
        responses.add(responses.GET, f"{BASE}/jobs/missing", json={"error": "not found"}, status=404)
        with pytest.raises(NotFoundError):
            client.get_job("missing")


# ------------------------------------------------------------------
# get_rubric
# ------------------------------------------------------------------

class TestGetRubric:
    @responses.activate
    def test_success(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/jobs/abc/rubric",
            json={"criteria": [{"name": "quality", "weight": 50}]},
            status=200,
        )
        rubric = client.get_rubric("abc")
        assert isinstance(rubric, Rubric)
        assert len(rubric.criteria) == 1


# ------------------------------------------------------------------
# submit / dry_run
# ------------------------------------------------------------------

class TestSubmit:
    @responses.activate
    def test_dry_run(self, client, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("print('hello')")
        responses.add(
            responses.POST,
            f"{BASE}/jobs/abc/submit/dry-run",
            json={"valid": True},
            status=200,
        )
        result = client.dry_run_submit("abc", files=[str(f)])
        assert result["valid"] is True

    @responses.activate
    def test_submit(self, client, tmp_path):
        f = tmp_path / "solution.py"
        f.write_text("x = 1")
        responses.add(
            responses.POST,
            f"{BASE}/jobs/abc/submit",
            json={"id": "sub1", "status": "submitted"},
            status=200,
        )
        sub = client.submit("abc", files=[str(f)])
        assert isinstance(sub, Submission)
        assert sub.id == "sub1"

    @responses.activate
    def test_submit_bundle(self, client):
        responses.add(
            responses.POST,
            f"{BASE}/jobs/abc/submit/bundle",
            json={"id": "sub2", "status": "received"},
            status=200,
        )
        result = client.submit_bundle("abc", payload={"data": "value"})
        assert result["id"] == "sub2"


# ------------------------------------------------------------------
# list_submissions / get_evaluation
# ------------------------------------------------------------------

class TestSubmissions:
    @responses.activate
    def test_list_submissions(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/jobs/abc/submissions",
            json=[{"id": "s1", "status": "pending"}, {"id": "s2", "status": "evaluated"}],
            status=200,
        )
        subs = client.list_submissions("abc")
        assert len(subs) == 2
        assert isinstance(subs[0], Submission)

    @responses.activate
    def test_get_evaluation(self, client):
        responses.add(
            responses.GET,
            f"{BASE}/jobs/abc/submissions/s1/evaluation",
            json={"id": "e1", "score": 85, "passed": True, "feedback": "Good work"},
            status=200,
        )
        ev = client.get_evaluation("abc", "s1")
        assert isinstance(ev, Evaluation)
        assert ev.score == 85
        assert ev.passed is True


# ------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------

class TestErrors:
    @responses.activate
    def test_auth_error_401(self, client):
        responses.add(responses.GET, f"{BASE}/jobs", json={"error": "unauthorized"}, status=401)
        with pytest.raises(AuthError):
            client.list_jobs()

    @responses.activate
    def test_auth_error_403(self, client):
        responses.add(responses.GET, f"{BASE}/jobs", json={"error": "forbidden"}, status=403)
        with pytest.raises(AuthError):
            client.list_jobs()

    @responses.activate
    def test_rate_limit(self, client):
        responses.add(responses.GET, f"{BASE}/jobs", json={"error": "rate limited"}, status=429)
        with pytest.raises(Exception):
            client.list_jobs()

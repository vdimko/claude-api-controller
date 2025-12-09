import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from main import (
    ConfigurationError,
    TaskStatus,
    app,
    get_optional_config,
    get_required_config,
    run_claude_command,
    tasks,
)


# Test API key for all tests
TEST_API_KEY = "test-api-key-12345"
TEST_AGENT_NAME = "test_agent"


@pytest.fixture(autouse=True)
def setup_api_key():
    """Set up test API key for all tests."""
    original_key = main.API_KEY
    main.API_KEY = TEST_API_KEY
    yield
    main.API_KEY = original_key


@pytest.fixture(autouse=True)
def clear_tasks():
    """Clear tasks store before each test."""
    tasks.clear()
    yield
    tasks.clear()


@pytest.fixture(autouse=True)
def setup_test_agent(tmp_path):
    """Create test agent directory for tests."""
    original_agents_dir = main.AGENTS_DIR
    test_agents_dir = tmp_path / "CUSTOM_AGENTS"
    test_agents_dir.mkdir()
    # Create test agent directory
    test_agent_dir = test_agents_dir / TEST_AGENT_NAME
    test_agent_dir.mkdir()
    main.AGENTS_DIR = str(test_agents_dir)
    yield test_agents_dir
    main.AGENTS_DIR = original_agents_dir


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return headers with valid API key."""
    return {"X-API-Key": TEST_API_KEY}


# =============================================================================
# Authentication Tests
# =============================================================================

class TestAuthentication:
    """Tests for API key authentication."""

    def test_missing_api_key_returns_401(self, client):
        """Request without API key should return 401."""
        response = client.get("/tasks")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_invalid_api_key_returns_403(self, client):
        """Request with wrong API key should return 403."""
        response = client.get("/tasks", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    def test_valid_api_key_allows_access(self, client, auth_headers):
        """Request with correct API key should succeed."""
        response = client.get("/tasks", headers=auth_headers)
        assert response.status_code == 200

    def test_health_endpoint_no_auth_required(self, client):
        """Health endpoint should work without authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_all_protected_endpoints_require_auth(self, client):
        """All endpoints except /health should require auth."""
        protected_endpoints = [
            ("POST", "/run", {"agent_name": TEST_AGENT_NAME, "prompt": "test"}),
            ("GET", "/status/fake-id", None),
            ("GET", "/tasks", None),
            ("DELETE", "/tasks/fake-id", None),
        ]

        for method, endpoint, json_data in protected_endpoints:
            if method == "POST":
                response = client.post(endpoint, json=json_data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert response.status_code in [401, 403], f"{method} {endpoint} should require auth"


# =============================================================================
# Health Endpoint Tests
# =============================================================================

class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_healthy(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


# =============================================================================
# Run Endpoint Tests
# =============================================================================

class TestRunEndpoint:
    """Tests for POST /run endpoint."""

    def test_run_creates_task_and_returns_id(self, client, auth_headers):
        """POST /run should create a task and return task_id."""
        response = client.post(
            "/run",
            json={"agent_name": TEST_AGENT_NAME, "prompt": "test prompt"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert len(data["task_id"]) == 36  # UUID length

    def test_run_stores_task_with_valid_status(self, client, auth_headers):
        """Created task should have a valid status."""
        response = client.post(
            "/run",
            json={"agent_name": TEST_AGENT_NAME, "prompt": "test prompt"},
            headers=auth_headers,
        )
        task_id = response.json()["task_id"]

        assert task_id in tasks
        # Task may be pending, running, or already completed depending on timing
        assert tasks[task_id]["status"] in [
            TaskStatus.PENDING,
            TaskStatus.RUNNING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
        ]
        assert "created_at" in tasks[task_id]

    def test_run_with_custom_timeout(self, client, auth_headers):
        """Custom timeout should be accepted."""
        response = client.post(
            "/run",
            json={"agent_name": TEST_AGENT_NAME, "prompt": "test", "timeout": 30},
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_run_requires_prompt(self, client, auth_headers):
        """Request without prompt should fail validation."""
        response = client.post(
            "/run",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    def test_run_empty_prompt(self, client, auth_headers):
        """Empty prompt should be accepted (validation is not strict)."""
        response = client.post(
            "/run",
            json={"agent_name": TEST_AGENT_NAME, "prompt": ""},
            headers=auth_headers,
        )
        # Empty string is technically valid
        assert response.status_code == 200


# =============================================================================
# Status Endpoint Tests
# =============================================================================

class TestStatusEndpoint:
    """Tests for GET /status/{task_id} endpoint."""

    def test_status_returns_task_info(self, client, auth_headers):
        """Should return task status and details."""
        # Create a task first
        response = client.post(
            "/run",
            json={"agent_name": TEST_AGENT_NAME, "prompt": "test"},
            headers=auth_headers,
        )
        task_id = response.json()["task_id"]

        # Get status
        response = client.get(f"/status/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["task_id"] == task_id
        # Status can be any valid status depending on timing
        assert data["status"] in ["pending", "running", "completed", "failed", "timeout"]
        assert "created_at" in data

    def test_status_not_found_returns_404(self, client, auth_headers):
        """Non-existent task should return 404."""
        response = client.get("/status/non-existent-id", headers=auth_headers)
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_status_shows_completed_result(self, client, auth_headers):
        """Completed task should show result."""
        # Manually create a completed task
        task_id = "test-completed-task"
        tasks[task_id] = {
            "status": TaskStatus.COMPLETED,
            "agent_name": TEST_AGENT_NAME,
            "result": "Hello from Claude",
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        response = client.get(f"/status/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"
        assert data["result"] == "Hello from Claude"
        assert data["error"] is None

    def test_status_shows_failed_error(self, client, auth_headers):
        """Failed task should show error message."""
        task_id = "test-failed-task"
        tasks[task_id] = {
            "status": TaskStatus.FAILED,
            "agent_name": TEST_AGENT_NAME,
            "result": None,
            "error": "Command failed",
            "created_at": "2024-01-01T00:00:00",
        }

        response = client.get(f"/status/{task_id}", headers=auth_headers)
        data = response.json()

        assert data["status"] == "failed"
        assert data["error"] == "Command failed"


# =============================================================================
# Tasks List Endpoint Tests
# =============================================================================

class TestTasksEndpoint:
    """Tests for GET /tasks endpoint."""

    def test_tasks_empty_initially(self, client, auth_headers):
        """Tasks list should be empty initially."""
        response = client.get("/tasks", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0
        assert data["tasks"] == {}

    def test_tasks_lists_all_tasks(self, client, auth_headers):
        """Should list all created tasks."""
        # Create multiple tasks
        for _ in range(3):
            client.post("/run", json={"agent_name": TEST_AGENT_NAME, "prompt": "test"}, headers=auth_headers)

        response = client.get("/tasks", headers=auth_headers)
        data = response.json()

        assert data["count"] == 3
        assert len(data["tasks"]) == 3

    def test_tasks_shows_status_and_created_at(self, client, auth_headers):
        """Task list should include status and created_at for each task."""
        response = client.post("/run", json={"agent_name": TEST_AGENT_NAME, "prompt": "test"}, headers=auth_headers)
        task_id = response.json()["task_id"]

        response = client.get("/tasks", headers=auth_headers)
        task_info = response.json()["tasks"][task_id]

        assert "status" in task_info
        assert "created_at" in task_info


# =============================================================================
# Delete Task Endpoint Tests
# =============================================================================

class TestDeleteTaskEndpoint:
    """Tests for DELETE /tasks/{task_id} endpoint."""

    def test_delete_removes_task(self, client, auth_headers):
        """Should remove task from store."""
        # Create a task
        response = client.post("/run", json={"agent_name": TEST_AGENT_NAME, "prompt": "test"}, headers=auth_headers)
        task_id = response.json()["task_id"]
        assert task_id in tasks

        # Delete it
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Task deleted"
        assert task_id not in tasks

    def test_delete_not_found_returns_404(self, client, auth_headers):
        """Deleting non-existent task should return 404."""
        response = client.delete("/tasks/non-existent", headers=auth_headers)
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]


# =============================================================================
# run_claude_command Function Tests
# =============================================================================

class TestRunClaudeCommand:
    """Tests for the run_claude_command async function."""

    @pytest.mark.asyncio
    async def test_successful_command_execution(self, setup_test_agent):
        """Successful command should set completed status and result."""
        task_id = "test-success"
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "agent_name": TEST_AGENT_NAME,
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        # Mock successful subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Hello World", b"")
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            await run_claude_command(task_id, TEST_AGENT_NAME, "test prompt", 30)

        assert tasks[task_id]["status"] == TaskStatus.COMPLETED
        assert tasks[task_id]["result"] == "Hello World"
        assert tasks[task_id]["error"] is None

    @pytest.mark.asyncio
    async def test_failed_command_execution(self, setup_test_agent):
        """Failed command should set failed status and error."""
        task_id = "test-fail"
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "agent_name": TEST_AGENT_NAME,
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Error message")
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            await run_claude_command(task_id, TEST_AGENT_NAME, "test prompt", 30)

        assert tasks[task_id]["status"] == TaskStatus.FAILED
        assert tasks[task_id]["error"] == "Error message"

    @pytest.mark.asyncio
    async def test_command_timeout(self, setup_test_agent):
        """Timed out command should set timeout status."""
        task_id = "test-timeout"
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "agent_name": TEST_AGENT_NAME,
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        mock_process = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                await run_claude_command(task_id, TEST_AGENT_NAME, "test prompt", 1)

        assert tasks[task_id]["status"] == TaskStatus.TIMEOUT
        assert "timed out" in tasks[task_id]["error"]

    @pytest.mark.asyncio
    async def test_claude_not_found(self, setup_test_agent):
        """Missing claude CLI should set failed status."""
        task_id = "test-not-found"
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "agent_name": TEST_AGENT_NAME,
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
            await run_claude_command(task_id, TEST_AGENT_NAME, "test prompt", 30)

        assert tasks[task_id]["status"] == TaskStatus.FAILED
        assert "not found" in tasks[task_id]["error"].lower()

    @pytest.mark.asyncio
    async def test_unexpected_exception(self, setup_test_agent):
        """Unexpected error should set failed status with error message."""
        task_id = "test-exception"
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "agent_name": TEST_AGENT_NAME,
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        with patch("asyncio.create_subprocess_exec", side_effect=RuntimeError("Unexpected")):
            await run_claude_command(task_id, TEST_AGENT_NAME, "test prompt", 30)

        assert tasks[task_id]["status"] == TaskStatus.FAILED
        assert "Unexpected" in tasks[task_id]["error"]

    @pytest.mark.asyncio
    async def test_status_changes_to_running(self, setup_test_agent):
        """Status should change to running when command starts."""
        task_id = "test-running"
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "agent_name": TEST_AGENT_NAME,
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        status_during_run = None

        async def capture_status(*args, **kwargs):
            nonlocal status_during_run
            status_during_run = tasks[task_id]["status"]
            mock = AsyncMock()
            mock.communicate.return_value = (b"done", b"")
            mock.returncode = 0
            return mock

        with patch("asyncio.create_subprocess_exec", side_effect=capture_status):
            await run_claude_command(task_id, TEST_AGENT_NAME, "test", 30)

        assert status_during_run == TaskStatus.RUNNING

    @pytest.mark.asyncio
    async def test_agent_directory_not_found(self, setup_test_agent):
        """Non-existent agent directory should set failed status."""
        task_id = "test-no-agent"
        tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "agent_name": "nonexistent_agent",
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00",
        }

        await run_claude_command(task_id, "nonexistent_agent", "test prompt", 30)

        assert tasks[task_id]["status"] == TaskStatus.FAILED
        assert "not found" in tasks[task_id]["error"].lower()


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow_with_mocked_claude(self, client, auth_headers):
        """Test complete workflow: create -> check status -> delete."""
        # Create task
        response = client.post(
            "/run",
            json={"agent_name": TEST_AGENT_NAME, "prompt": "Hello"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        # Check it appears in list
        response = client.get("/tasks", headers=auth_headers)
        assert task_id in response.json()["tasks"]

        # Check status
        response = client.get(f"/status/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        # Delete
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify deleted
        response = client.get(f"/status/{task_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_multiple_concurrent_tasks(self, client, auth_headers):
        """Should handle multiple tasks simultaneously."""
        task_ids = []

        # Create 5 tasks
        for i in range(5):
            response = client.post(
                "/run",
                json={"agent_name": TEST_AGENT_NAME, "prompt": f"Task {i}"},
                headers=auth_headers,
            )
            task_ids.append(response.json()["task_id"])

        # All should exist
        response = client.get("/tasks", headers=auth_headers)
        assert response.json()["count"] == 5

        for task_id in task_ids:
            assert task_id in response.json()["tasks"]


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfiguration:
    """Tests for configuration loading."""

    def test_get_required_config_returns_value(self):
        """Should return value when env var is set."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            assert get_required_config("TEST_VAR") == "test_value"

    def test_get_required_config_raises_on_missing(self):
        """Should raise ConfigurationError when env var is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Make sure the var doesn't exist
            os.environ.pop("NONEXISTENT_VAR", None)
            with pytest.raises(ConfigurationError) as exc_info:
                get_required_config("NONEXISTENT_VAR")
            assert "NONEXISTENT_VAR" in str(exc_info.value)
            assert "not set" in str(exc_info.value)

    def test_get_optional_config_returns_value(self):
        """Should return value when env var is set."""
        with patch.dict(os.environ, {"TEST_VAR": "custom_value"}):
            assert get_optional_config("TEST_VAR", "default") == "custom_value"

    def test_get_optional_config_returns_default(self):
        """Should return default when env var is not set."""
        os.environ.pop("NONEXISTENT_VAR", None)
        assert get_optional_config("NONEXISTENT_VAR", "default_value") == "default_value"

    def test_configuration_error_message(self):
        """ConfigurationError should have descriptive message."""
        error = ConfigurationError("Test message")
        assert str(error) == "Test message"

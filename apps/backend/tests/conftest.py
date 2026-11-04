"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from apps.backend.src.models.entities import (
    User,
    Project,
    Workflow,
    Task,
    Artifact,
    Deployment,
    ApprovalRequest,
    AgentExecution,
    UserRole,
    ProjectStatus,
    WorkflowStatus,
    WorkflowPhase,
    TaskStatus,
    AgentRole,
    ArtifactType,
    DeploymentStatus,
    ApprovalStatus,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    session.scalars = MagicMock()
    return session


@pytest.fixture
def sample_user():
    """Create a sample user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.DEVELOPER,
        is_active=True,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_project(sample_user):
    """Create a sample project."""
    return Project(
        id=uuid4(),
        name="Test Project",
        description="A test project",
        repository_url="https://github.com/test/repo",
        technology_stack=["Python", "FastAPI", "PostgreSQL"],
        requirements={"feature": "auth"},
        status=ProjectStatus.ACTIVE,
        settings={},
        owner_id=sample_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_workflow(sample_project):
    """Create a sample workflow."""
    return Workflow(
        id=uuid4(),
        name="Test Workflow",
        description="A test workflow",
        status=WorkflowStatus.RUNNING,
        current_phase=WorkflowPhase.PLANNING,
        progress=0,
        initial_state={},
        state={},
        project_id=sample_project.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_task(sample_workflow, sample_project):
    """Create a sample task."""
    return Task(
        id=uuid4(),
        title="Test Task",
        description="A test task",
        role=AgentRole.BACKEND,
        priority="medium",
        dependencies=[],
        estimated_effort="2h",
        tags=["api"],
        status=TaskStatus.PENDING,
        project_id=sample_project.id,
        workflow_id=sample_workflow.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_artifact(sample_task, sample_project, sample_user):
    """Create a sample artifact."""
    return Artifact(
        id=uuid4(),
        name="test.py",
        type=ArtifactType.CODE,
        content="print('hello')",
        metadata={},
        file_path=None,
        mime_type="text/x-python",
        size_bytes=13,
        version=1,
        task_id=sample_task.id,
        project_id=sample_project.id,
        created_by=sample_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_deployment(sample_workflow, sample_project, sample_user):
    """Create a sample deployment."""
    return Deployment(
        id=uuid4(),
        environment="staging",
        strategy="rolling",
        config={},
        status=DeploymentStatus.PENDING,
        version="v1.0.0",
        logs=[],
        project_id=sample_project.id,
        workflow_id=sample_workflow.id,
        triggered_by=sample_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_approval(sample_workflow, sample_task):
    """Create a sample approval request."""
    return ApprovalRequest(
        id=uuid4(),
        title="Deploy to production?",
        description="Ready to deploy",
        options=[{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}],
        status=ApprovalStatus.PENDING,
        requested_by=AgentRole.DEVOPS,
        workflow_id=sample_workflow.id,
        task_id=sample_task.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_agent_execution(sample_task):
    """Create a sample agent execution."""
    return AgentExecution(
        id=uuid4(),
        agent_role=AgentRole.BACKEND,
        status=TaskStatus.COMPLETED,
        input_data={"task": "implement api"},
        output_data={"files": ["api.py"]},
        tokens_used=1000,
        cost_usd=0.01,
        llm_provider="openai",
        llm_model="gpt-4-turbo-preview",
        duration_seconds=30.5,
        task_id=sample_task.id,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "asyncio: Async tests")
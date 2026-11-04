"""
Unit tests for shared schemas.
"""
import pytest
from uuid import uuid4
from datetime import datetime

from services.shared.schemas import (
    TaskStatus,
    AgentRole,
    WorkflowPhase,
    Priority,
    ArtifactType,
    Task,
    TaskCreate,
    TaskUpdate,
    Artifact,
    ArtifactCreate,
    Project,
    ProjectCreate,
    Workflow,
    WorkflowCreate,
    AgentMessage,
    ApprovalRequest,
    ApprovalResponse,
    Deployment,
    DeploymentCreate,
    WorkflowMetrics,
    HealthCheck,
)


class TestTaskSchema:
    """Tests for Task schema."""

    def test_task_create_valid(self):
        """Test creating a valid task."""
        project_id = uuid4()
        task = TaskCreate(
            title="Test Task",
            description="Test Description",
            role=AgentRole.BACKEND,
            project_id=project_id,
        )
        assert task.title == "Test Task"
        assert task.role == AgentRole.BACKEND
        assert task.project_id == project_id
        assert task.priority == Priority.MEDIUM
        assert task.dependencies == []

    def test_task_create_with_dependencies(self):
        """Test creating task with dependencies."""
        dep_id = uuid4()
        task = TaskCreate(
            title="Dependent Task",
            description="Has dependencies",
            role=AgentRole.FRONTEND,
            project_id=uuid4(),
            dependencies=[dep_id],
        )
        assert dep_id in task.dependencies

    def test_task_update_partial(self):
        """Test partial task update."""
        update = TaskUpdate(
            title="Updated Title",
            status=TaskStatus.COMPLETED,
        )
        assert update.title == "Updated Title"
        assert update.status == TaskStatus.COMPLETED
        assert update.description is None

    def test_task_full(self):
        """Test complete task schema."""
        task_id = uuid4()
        project_id = uuid4()
        task = Task(
            id=task_id,
            title="Full Task",
            description="Complete task",
            role=AgentRole.BACKEND,
            project_id=project_id,
            status=TaskStatus.RUNNING,
            progress=50,
        )
        assert task.id == task_id
        assert task.progress == 50
        assert task.artifacts == []


class TestArtifactSchema:
    """Tests for Artifact schema."""

    def test_artifact_create_valid(self):
        """Test creating a valid artifact."""
        artifact = ArtifactCreate(
            task_id=uuid4(),
            project_id=uuid4(),
            created_by=uuid4(),
            name="test.py",
            type=ArtifactType.CODE,
            content="print('hello')",
        )
        assert artifact.name == "test.py"
        assert artifact.type == ArtifactType.CODE

    def test_artifact_full(self):
        """Test complete artifact schema."""
        artifact = Artifact(
            id=uuid4(),
            task_id=uuid4(),
            project_id=uuid4(),
            created_by=uuid4(),
            name="test.py",
            type=ArtifactType.CODE,
            content="print('hello')",
            version=1,
        )
        assert artifact.version == 1
        assert artifact.parent_id is None


class TestProjectSchema:
    """Tests for Project schema."""

    def test_project_create_valid(self):
        """Test creating a valid project."""
        project = ProjectCreate(
            name="Test Project",
            description="A test project",
            owner_id=uuid4(),
        )
        assert project.name == "Test Project"
        assert project.technology_stack == []

    def test_project_full(self):
        """Test complete project schema."""
        project = Project(
            id=uuid4(),
            name="Full Project",
            description="Complete project",
            owner_id=uuid4(),
            status="active",
            technology_stack=["Python", "FastAPI"],
        )
        assert "Python" in project.technology_stack


class TestWorkflowSchema:
    """Tests for Workflow schema."""

    def test_workflow_create_valid(self):
        """Test creating a valid workflow."""
        workflow = WorkflowCreate(
            project_id=uuid4(),
            name="Test Workflow",
            description="A test workflow",
        )
        assert workflow.name == "Test Workflow"

    def test_workflow_full(self):
        """Test complete workflow schema."""
        workflow = Workflow(
            id=uuid4(),
            project_id=uuid4(),
            name="Full Workflow",
            description="Complete workflow",
            status="running",
            current_phase=WorkflowPhase.IMPLEMENTATION,
            progress=50,
        )
        assert workflow.current_phase == WorkflowPhase.IMPLEMENTATION


class TestAgentMessageSchema:
    """Tests for AgentMessage schema."""

    def test_agent_message_valid(self):
        """Test creating a valid agent message."""
        message = AgentMessage(
            id=uuid4(),
            task_id=uuid4(),
            from_agent=AgentRole.PLANNER,
            to_agent=AgentRole.BACKEND,
            message_type="request",
            payload={"action": "implement"},
        )
        assert message.from_agent == AgentRole.PLANNER
        assert message.to_agent == AgentRole.BACKEND
        assert message.confidence == 1.0


class TestApprovalSchema:
    """Tests for Approval schemas."""

    def test_approval_request(self):
        """Test approval request creation."""
        request = ApprovalRequest(
            workflow_id=uuid4(),
            task_id=uuid4(),
            title="Deploy to production?",
            description="Ready to deploy",
            options=[{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}],
            requested_by=AgentRole.DEVOPS,
        )
        assert len(request.options) == 2

    def test_approval_response(self):
        """Test approval response."""
        response = ApprovalResponse(
            request_id=uuid4(),
            approved=True,
            selected_option="yes",
            decided_by=uuid4(),
        )
        assert response.approved is True
        assert response.selected_option == "yes"


class TestDeploymentSchema:
    """Tests for Deployment schema."""

    def test_deployment_create_valid(self):
        """Test creating a valid deployment."""
        deployment = DeploymentCreate(
            project_id=uuid4(),
            workflow_id=uuid4(),
            environment="staging",
            strategy="rolling",
            triggered_by=uuid4(),
        )
        assert deployment.environment == "staging"
        assert deployment.strategy == "rolling"

    def test_deployment_full(self):
        """Test complete deployment schema."""
        deployment = Deployment(
            id=uuid4(),
            project_id=uuid4(),
            workflow_id=uuid4(),
            environment="production",
            strategy="blue_green",
            version="v1.0.0",
            triggered_by=uuid4(),
            status="completed",
        )
        assert deployment.version == "v1.0.0"


class TestMetricsSchema:
    """Tests for Metrics schema."""

    def test_workflow_metrics(self):
        """Test workflow metrics."""
        metrics = WorkflowMetrics(
            workflow_id=uuid4(),
            total_tasks=10,
            completed_tasks=8,
            failed_tasks=1,
            total_tokens=5000,
            total_cost_usd=0.15,
        )
        assert metrics.total_tasks == 10
        assert metrics.completed_tasks == 8

    def test_health_check(self):
        """Test health check schema."""
        health = HealthCheck(
            status="healthy",
            service="agentforge-backend",
            version="0.1.0",
        )
        assert health.status == "healthy"
        assert health.service == "agentforge-backend"


class TestEnums:
    """Tests for enum values."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_agent_role_values(self):
        """Test AgentRole enum values."""
        assert AgentRole.PLANNER == "planner"
        assert AgentRole.BACKEND == "backend"
        assert AgentRole.REVIEWER == "reviewer"

    def test_workflow_phase_values(self):
        """Test WorkflowPhase enum values."""
        assert WorkflowPhase.PLANNING == "planning"
        assert WorkflowPhase.DEPLOYMENT == "deployment"

    def test_priority_values(self):
        """Test Priority enum values."""
        assert Priority.LOW == "low"
        assert Priority.HIGH == "high"
        assert Priority.CRITICAL == "critical"

    def test_artifact_type_values(self):
        """Test ArtifactType enum values."""
        assert ArtifactType.CODE == "code"
        assert ArtifactType.DOCUMENT == "document"
        assert ArtifactType.TEST == "test"
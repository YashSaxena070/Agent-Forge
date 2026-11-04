"""
End-to-end test for the full AgentForge pipeline.
"""
import asyncio
import json
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from apps.backend.src.orchestration.langgraph.executor import WorkflowExecutor
from apps.backend.src.orchestration.state import create_initial_state
from apps.backend.src.agents.base import AgentRegistry
from apps.backend.src.models.entities import (
    User, Project, Workflow, Task,
    UserRole, ProjectStatus, WorkflowStatus, WorkflowPhase, TaskStatus, AgentRole
)
from apps.backend.src.core.llm import LLMResponse, LLMProviderFactory
from apps.backend.src.core.tools import get_tool_executor


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    return session


@pytest.fixture
def sample_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.DEVELOPER,
        is_active=True,
    )


@pytest.fixture
def sample_project(sample_user):
    return Project(
        id=uuid4(),
        name="Test Project",
        description="E2E test project",
        technology_stack=["Python", "FastAPI", "PostgreSQL"],
        requirements={"feature": "auth"},
        status=ProjectStatus.ACTIVE,
        owner_id=sample_user.id,
    )


@pytest.fixture
def sample_workflow(sample_project, sample_user):
    return Workflow(
        id=uuid4(),
        name="Test Workflow",
        description="E2E test workflow",
        status=WorkflowStatus.CREATED,
        current_phase=WorkflowPhase.PLANNING,
        progress=0,
        initial_state={},
        state={},
        project_id=sample_project.id,
    )


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.call_count = 0
        self.responses = []
    
    def set_response(self, response: LLMResponse):
        self.responses.append(response)
    
    async def complete(self, messages, response_model=None, **kwargs):
        self.call_count += 1
        if self.responses:
            return self.responses.pop(0)
        
        # Default responses based on agent role
        agent_role = kwargs.get("agent_role", "unknown")
        
        if agent_role == "planner":
            return LLMResponse(
                content='{"milestones": [{"name": "Foundation", "description": "Setup", "deliverables": ["Architecture"], "tasks": [{"title": "Create Architecture", "description": "Design system", "role": "architect", "priority": "high", "dependencies": [], "estimated_effort": "4h", "tags": ["architecture"]}]}], "architecture_decisions": [], "risks": []}',
                parsed=MagicMock(model_dump=lambda: {
                    "milestones": [{
                        "name": "Foundation",
                        "description": "Setup",
                        "deliverables": ["Architecture"],
                        "tasks": [{
                            "title": "Create Architecture",
                            "description": "Design system",
                            "role": "architect",
                            "priority": "high",
                            "dependencies": [],
                            "estimated_effort": "4h",
                            "tags": ["architecture"]
                        }]
                    }],
                    "architecture_decisions": [],
                    "risks": []
                }),
                tokens_used=1000,
                cost_usd=0.01,
                model="gpt-4-turbo-preview",
                provider="openai",
            )
        elif agent_role == "architect":
            return LLMResponse(
                content='{"architecture": {"style": "modular_monolith", "components": [{"name": "api", "type": "service", "technology": "FastAPI", "responsibilities": ["REST API"], "interfaces": ["REST"]}], "communication": {"sync": ["REST"]}, "data_stores": [{"name": "db", "type": "postgresql", "purpose": "Data"}], "infrastructure": {"containerization": "docker"}}, "api_design": {"style": "REST", "endpoints": []}, "data_models": [], "adrs": [], "security_considerations": [], "scalability_considerations": []}',
                parsed=MagicMock(model_dump=lambda: {
                    "architecture": {"style": "modular_monolith", "components": []},
                    "api_design": {"style": "REST", "endpoints": []},
                    "data_models": [],
                    "adrs": [],
                    "security_considerations": [],
                    "scalability_considerations": [],
                }),
                tokens_used=2000,
                cost_usd=0.02,
                model="gpt-4-turbo-preview",
                provider="openai",
            )
        elif agent_role == "backend":
            return LLMResponse(
                content='{"files": [{"path": "src/main.py", "content": "print(\\"hello\\")", "language": "python"}], "database_migrations": [], "tests": [], "dependencies": [], "configuration": {}, "deployment_notes": ""}',
                parsed=MagicMock(model_dump=lambda: {
                    "files": [{"path": "src/main.py", "content": "print(\"hello\")", "language": "python"}],
                    "database_migrations": [],
                    "tests": [],
                    "dependencies": [],
                    "configuration": {},
                    "deployment_notes": "",
                }),
                tokens_used=3000,
                cost_usd=0.03,
                model="gpt-4-turbo-preview",
                provider="openai",
            )
        elif agent_role == "devops":
            return LLMResponse(
                content='{"kubernetes_manifests": [], "dockerfile": {"path": "Dockerfile", "content": "FROM python:3.11", "language": "dockerfile"}, "docker_compose": {"path": "docker-compose.yml", "content": "version: 3.8", "language": "yaml"}, "github_actions": {"path": ".github/workflows/ci.yaml", "content": "name: CI", "language": "yaml"}, "helm_chart": [], "deployment_script": {"path": "deploy.sh", "content": "echo deploy", "language": "bash"}, "rollback_script": {"path": "rollback.sh", "content": "echo rollback", "language": "bash"}}',
                parsed=MagicMock(model_dump=lambda: {
                    "kubernetes_manifests": [],
                    "dockerfile": {"path": "Dockerfile", "content": "FROM python:3.11", "language": "dockerfile"},
                    "docker_compose": {"path": "docker-compose.yml", "content": "version: 3.8", "language": "yaml"},
                    "github_actions": {"path": ".github/workflows/ci.yaml", "content": "name: CI", "language": "yaml"},
                    "helm_chart": [],
                    "deployment_script": {"path": "deploy.sh", "content": "echo deploy", "language": "bash"},
                    "rollback_script": {"path": "rollback.sh", "content": "echo rollback", "language": "bash"},
                }),
                tokens_used=2500,
                cost_usd=0.025,
                model="gpt-4-turbo-preview",
                provider="openai",
            )
        
        return LLMResponse(
            content="{}",
            tokens_used=100,
            cost_usd=0.001,
            model="gpt-4-turbo-preview",
            provider="openai",
        )


@pytest.mark.asyncio
async def test_planner_agent_creates_plan(mock_db_session, sample_project, sample_workflow):
    """Test that planner agent creates a valid plan."""
    from apps.backend.src.agents.planner import PlannerAgent
    from apps.backend.src.core.llm import LLMProviderFactory
    
    # Setup mock LLM
    mock_provider = MockLLMProvider()
    LLMProviderFactory._providers["openai"] = mock_provider
    
    # Register agent
    AgentRegistry._agents.clear()
    AgentRegistry._instances.clear()
    planner = PlannerAgent()
    
    # Execute
    task_id = uuid4()
    input_data = {
        "product_request": "Build a task management app",
        "project_context": {"tech_stack": ["Python", "FastAPI"]},
        "existing_state": {},
    }
    
    result = await planner._run_with_tracking(task_id, input_data, mock_db_session)
    
    assert result.success is True
    assert "plan" in result.output
    assert "tasks" in result.output
    assert len(result.output["tasks"]) > 0
    assert result.output["tasks"][0]["role"] == "architect"
    
    # Verify DB calls
    mock_db_session.add.assert_called()
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_architect_agent_creates_architecture(mock_db_session, sample_workflow):
    """Test that architect agent creates architecture."""
    from apps.backend.src.agents.architect import ArchitectAgent
    from apps.backend.src.core.llm import LLMProviderFactory
    
    mock_provider = MockLLMProvider()
    LLMProviderFactory._providers["openai"] = mock_provider
    
    AgentRegistry._agents.clear()
    AgentRegistry._instances.clear()
    architect = ArchitectAgent()
    
    task_id = uuid4()
    input_data = {
        "user_stories": [{"id": "US-001", "title": "User login"}],
        "requirements": {"auth": "JWT"},
        "tech_stack": ["FastAPI", "PostgreSQL"],
    }
    
    result = await architect._run_with_tracking(task_id, input_data, mock_db_session)
    
    assert result.success is True
    assert "result" in result.output
    assert "architecture" in result.output["result"]
    assert len(result.artifacts) > 0


@pytest.mark.asyncio
async def test_backend_agent_generates_code(mock_db_session):
    """Test that backend agent generates code."""
    from apps.backend.src.agents.backend import BackendAgent
    from apps.backend.src.core.llm import LLMProviderFactory
    
    mock_provider = MockLLMProvider()
    LLMProviderFactory._providers["openai"] = mock_provider
    
    AgentRegistry._agents.clear()
    AgentRegistry._instances.clear()
    backend = BackendAgent()
    
    task_id = uuid4()
    input_data = {
        "task_title": "Implement Auth API",
        "task_description": "Create register/login endpoints",
        "architecture": {"components": [{"name": "auth", "technology": "FastAPI"}]},
        "api_spec": {"endpoints": [{"path": "/auth/register", "method": "POST"}]},
        "tech_stack": ["FastAPI", "PostgreSQL"],
    }
    
    result = await backend._run_with_tracking(task_id, input_data, mock_db_session)
    
    assert result.success is True
    assert len(result.artifacts) > 0
    # Check that code files were generated
    code_artifacts = [a for a in result.artifacts if a["type"] == "code"]
    assert len(code_artifacts) > 0


@pytest.mark.asyncio
async def test_devops_agent_generates_deployment(mock_db_session):
    """Test that DevOps agent generates deployment configs."""
    from apps.backend.src.agents.devops import DevOpsAgent
    from apps.backend.src.core.llm import LLMProviderFactory
    
    mock_provider = MockLLMProvider()
    LLMProviderFactory._providers["openai"] = mock_provider
    
    AgentRegistry._agents.clear()
    AgentRegistry._instances.clear()
    devops = DevOpsAgent()
    
    task_id = uuid4()
    input_data = {
        "architecture": {"components": [{"name": "api", "technology": "FastAPI"}]},
        "tech_stack": ["FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
        "environment": "staging",
    }
    
    result = await devops._run_with_tracking(task_id, input_data, mock_db_session)
    
    assert result.success is True
    assert len(result.artifacts) > 0
    # Check for Dockerfile, K8s manifests, etc.
    config_artifacts = [a for a in result.artifacts if a["type"] == "config"]
    assert len(config_artifacts) > 0


@pytest.mark.asyncio
async def test_full_pipeline_execution(mock_db_session, sample_project, sample_workflow, sample_user):
    """Test full pipeline execution through LangGraph."""
    from apps.backend.src.orchestration.langgraph.executor import WorkflowExecutor
    
    # Mock all LLM providers
    mock_provider = MockLLMProvider()
    LLMProviderFactory._providers["openai"] = mock_provider
    
    # Register all agents
    AgentRegistry._agents.clear()
    AgentRegistry._instances.clear()
    
    from apps.backend.src.agents.planner import PlannerAgent
    from apps.backend.src.agents.architect import ArchitectAgent
    from apps.backend.src.agents.backend import BackendAgent
    from apps.backend.src.agents.devops import DevOpsAgent
    
    PlannerAgent()
    ArchitectAgent()
    BackendAgent()
    DevOpsAgent()
    
    # Create executor
    executor = WorkflowExecutor(mock_db_session)
    
    # Create initial state
    initial_state = create_initial_state(
        workflow_id=sample_workflow.id,
        user_id=sample_user.id,
        input_data={"product_request": "Build a simple API"},
        project_id=sample_project.id,
    )
    
    # Execute (this would run through the graph in real implementation)
    # For testing, we verify the executor can be created
    assert executor is not None
    assert executor.app is not None


@pytest.mark.asyncio
async def test_tool_executor():
    """Test tool executor with local tools."""
    from apps.backend.src.core.tools import ToolExecutor, LocalToolRegistry
    
    executor = ToolExecutor()
    await executor.initialize()
    
    # Test local tool execution
    result = await executor.execute("filesystem", {
        "operation": "write",
        "path": "test.txt",
        "content": "Hello World"
    })
    
    assert result.get("success") is True
    
    # Read back
    result = await executor.execute("filesystem", {
        "operation": "read",
        "path": "test.txt"
    })
    
    assert result == "Hello World"
    
    await executor.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
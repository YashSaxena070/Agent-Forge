"""
Unit tests for agent base classes.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from apps.backend.src.agents.base import (
    BaseAgent,
    AgentResult,
    Tool,
    AgentRegistry,
    agent_role,
)
from apps.backend.src.models.entities import AgentRole


class TestAgentResult:
    """Tests for AgentResult."""

    def test_agent_result_success(self):
        """Test successful agent result."""
        result = AgentResult(
            success=True,
            output={"key": "value"},
            artifacts=[{"name": "test.py"}],
            next_actions=[{"action": "next"}],
            confidence=0.9,
        )
        assert result.success is True
        assert result.confidence == 0.9

    def test_agent_result_failure(self):
        """Test failed agent result."""
        result = AgentResult(
            success=False,
            error="Something went wrong",
            confidence=0.0,
        )
        assert result.success is False
        assert result.error == "Something went wrong"


class TestTool:
    """Tests for Tool definition."""

    def test_tool_creation(self):
        """Test creating a tool."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            required=[],
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_registry_starts_empty(self):
        """Test registry starts empty."""
        # Clear any existing registrations
        AgentRegistry._agents.clear()
        AgentRegistry._instances.clear()
        
        assert AgentRegistry.get_all_agents() == []
        assert AgentRegistry.get_all_roles() == []

    def test_register_agent(self):
        """Test registering an agent."""
        AgentRegistry._agents.clear()
        AgentRegistry._instances.clear()
        
        @agent_role(AgentRole.PLANNER)
        class TestPlannerAgent(BaseAgent):
            role = AgentRole.PLANNER
            name = "Test Planner"
            description = "Test planner agent"
            
            async def execute(self, task_id, input_data, db_session=None):
                return AgentResult(success=True, output={})
        
        agent = AgentRegistry.get_agent(AgentRole.PLANNER)
        assert agent is not None
        assert agent.name == "Test Planner"
        
        agents = AgentRegistry.get_all_agents()
        assert len(agents) == 1
        
        roles = AgentRegistry.get_all_roles()
        assert AgentRole.PLANNER in roles


class TestBaseAgent:
    """Tests for BaseAgent."""

    @pytest.mark.asyncio
    async def test_run_with_tracking_success(self):
        """Test successful agent execution with tracking."""
        
        class TestAgent(BaseAgent):
            role = AgentRole.PLANNER
            name = "Test"
            description = "Test"
            
            async def execute(self, task_id, input_data, db_session=None):
                return AgentResult(
                    success=True,
                    output={"result": "done"},
                    artifacts=[{"name": "test.py"}],
                )
        
        agent = TestAgent()
        task_id = uuid4()
        
        # Mock database session
        mock_db = AsyncMock()
        
        result = await agent._run_with_tracking(task_id, {}, mock_db)
        
        assert result.success is True
        assert result.output["result"] == "done"
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_run_with_tracking_failure(self):
        """Test agent execution failure with tracking."""
        
        class FailingAgent(BaseAgent):
            role = AgentRole.PLANNER
            name = "Failing"
            description = "Failing agent"
            
            async def execute(self, task_id, input_data, db_session=None):
                raise ValueError("Test error")
        
        agent = FailingAgent()
        task_id = uuid4()
        mock_db = AsyncMock()
        
        result = await agent._run_with_tracking(task_id, {}, mock_db)
        
        assert result.success is False
        assert "Test error" in result.error
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_build_prompt(self):
        """Test prompt building."""
        
        class TestAgent(BaseAgent):
            role = AgentRole.PLANNER
            name = "Test"
            description = "Test"
            prompt_template = "Hello {name}, your task is {task}"
            
            async def execute(self, task_id, input_data, db_session=None):
                return AgentResult(success=True, output={})
        
        agent = TestAgent()
        prompt = agent._build_prompt({"name": "John", "task": "code"})
        assert prompt == "Hello John, your task is code"

    def test_validate_output(self):
        """Test output validation."""
        
        class TestAgent(BaseAgent):
            role = AgentRole.PLANNER
            name = "Test"
            description = "Test"
            
            async def execute(self, task_id, input_data, db_session=None):
                return AgentResult(success=True, output={})
        
        agent = TestAgent()
        # Default validation always passes
        assert agent._validate_output({"any": "data"}) is True
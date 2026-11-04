"""
Base agent classes and registry.
"""
import abc
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from pydantic import BaseModel, Field

from apps.backend.src.models.entities import AgentRole, TaskStatus, AgentExecution, Task
from apps.backend.src.core.database import get_db_session
from apps.backend.src.core.telemetry import record_agent_metrics
from services.shared.schemas import AgentRole as SharedAgentRole


class Tool(BaseModel):
    """Tool definition for agents."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Result of agent execution."""
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    next_actions: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class BaseAgent(abc.ABC):
    """Base class for all specialized agents."""
    
    role: AgentRole
    name: str
    description: str
    capabilities: List[str] = []
    tools: List[Tool] = []
    prompt_template: str = ""
    
    def __init__(self):
        self._db_session = None
    
    @property
    def db(self):
        """Get database session."""
        if self._db_session is None:
            self._db_session = get_db_session()
        return self._db_session
    
    @abc.abstractmethod
    async def execute(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        db_session=None,
    ) -> AgentResult:
        """Execute the agent's main logic."""
        pass
    
    async def _run_with_tracking(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        db_session=None,
    ) -> AgentResult:
        """Run agent with execution tracking."""
        start_time = datetime.utcnow()
        execution = None
        
        try:
            # Create execution record
            if db_session:
                execution = AgentExecution(
                    agent_role=self.role,
                    task_id=task_id,
                    input_data=input_data,
                    status=TaskStatus.RUNNING,
                    started_at=start_time,
                )
                db_session.add(execution)
                await db_session.commit()
                await db_session.refresh(execution)
            
            # Execute agent logic
            result = await self.execute(task_id, input_data, db_session)
            
            # Update execution record
            if execution:
                execution.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                execution.output_data = result.output
                execution.error = result.error
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
                
                # Calculate tokens and cost (placeholder)
                execution.tokens_used = result.output.get("tokens_used", 0)
                execution.cost_usd = result.output.get("cost_usd", 0.0)
                execution.llm_provider = result.output.get("llm_provider")
                execution.llm_model = result.output.get("llm_model")
                
                await db_session.commit()
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            record_agent_metrics(
                agent_role=self.role.value,
                duration=duration,
                status="completed" if result.success else "failed",
                tokens=execution.tokens_used if execution else 0,
                cost=execution.cost_usd if execution else 0.0,
            )
            
            return result
            
        except Exception as e:
            # Update execution record on error
            if execution:
                execution.status = TaskStatus.FAILED
                execution.error = str(e)
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
                await db_session.commit()
            
            # Record error metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            record_agent_metrics(
                agent_role=self.role.value,
                duration=duration,
                status="failed",
            )
            
            return AgentResult(
                success=False,
                error=str(e),
                confidence=0.0,
            )
    
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4000,
        response_format: str = "json",
    ) -> Dict[str, Any]:
        """Call LLM with structured output."""
        # This would integrate with the LLM provider
        # For now, return a mock response
        return {
            "content": "{}",
            "tokens_used": 100,
            "cost_usd": 0.001,
            "llm_provider": "openai",
            "llm_model": "gpt-4-turbo-preview",
        }
    
    def _build_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build the complete prompt for the agent."""
        return self.prompt_template.format(**input_data)
    
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate agent output against expected schema."""
        # Override in subclasses for specific validation
        return True


class AgentRegistry:
    """Registry for all agents."""
    
    _agents: Dict[AgentRole, Type[BaseAgent]] = {}
    _instances: Dict[AgentRole, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent_class: Type[BaseAgent]):
        """Register an agent class."""
        instance = agent_class()
        cls._agents[instance.role] = agent_class
        cls._instances[instance.role] = instance
    
    @classmethod
    def get_agent(cls, role: AgentRole) -> Optional[BaseAgent]:
        """Get agent instance by role."""
        return cls._instances.get(role)
    
    @classmethod
    def get_agent_class(cls, role: AgentRole) -> Optional[Type[BaseAgent]]:
        """Get agent class by role."""
        return cls._agents.get(role)
    
    @classmethod
    def get_all_agents(cls) -> List[BaseAgent]:
        """Get all registered agents."""
        return list(cls._instances.values())
    
    @classmethod
    def get_all_roles(cls) -> List[AgentRole]:
        """Get all registered agent roles."""
        return list(cls._agents.keys())


def agent_role(role: AgentRole):
    """Decorator to register an agent."""
    def decorator(cls: Type[BaseAgent]):
        cls.role = role
        AgentRegistry.register(cls)
        return cls
    return decorator
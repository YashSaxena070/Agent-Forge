"""
Planner Agent with real LLM integration.
"""
import json
from typing import Any, Dict, List
from uuid import UUID, uuid4

from apps.backend.src.agents.base import BaseAgent, AgentResult, agent_role
from apps.backend.src.agents.prompts import PLANNER_PROMPT
from apps.backend.src.core.llm import LLMProviderFactory, PlanOutput
from apps.backend.src.models.entities import AgentRole
from apps.backend.src.core.tools import get_tool_executor
from apps.backend.src.core.telemetry import record_agent_metrics


@agent_role(AgentRole.PLANNER)
class PlannerAgent(BaseAgent):
    """Planner Agent - Creates project plans with real LLM calls."""
    
    role = AgentRole.PLANNER
    name = "Planner"
    description = "Decomposes product requests into milestones, assigns work to specialized agents, estimates dependencies"
    capabilities = [
        "requirements_analysis",
        "task_decomposition",
        "dependency_estimation",
        "milestone_planning",
        "resource_allocation",
    ]
    
    async def execute(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        db_session=None,
    ) -> AgentResult:
        """Execute the planner agent with real LLM."""
        product_request = input_data.get("product_request", "")
        project_context = input_data.get("project_context", {})
        existing_state = input_data.get("existing_state", {})
        constraints = input_data.get("constraints", {})
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": "You are an expert software project planner. Output valid JSON only."},
            {"role": "user", "content": PLANNER_PROMPT.format(
                product_request=product_request,
                project_context=json.dumps(project_context, indent=2),
                existing_state=json.dumps(existing_state, indent=2),
                constraints=json.dumps(constraints, indent=2),
            )},
        ]
        
        try:
            # Call LLM with structured output
            response = await LLMProviderFactory.complete(
                messages=messages,
                response_model=PlanOutput,
                agent_role="planner",
                temperature=0.2,
                max_tokens=8000,
            )
            
            if not response.parsed:
                return AgentResult(
                    success=False,
                    error="Failed to parse planner output",
                    confidence=0.0,
                )
            
            plan = response.parsed.model_dump()
            
            # Validate and enrich plan
            validated_plan = self._validate_and_enrich_plan(plan)
            
            # Flatten tasks for workflow
            all_tasks = []
            for milestone in validated_plan.get("milestones", []):
                for task in milestone.get("tasks", []):
                    task["milestone"] = milestone["name"]
                    all_tasks.append(task)
            
            return AgentResult(
                success=True,
                output={
                    "plan": validated_plan,
                    "tasks": all_tasks,
                    "tokens_used": response.tokens_used,
                    "cost_usd": response.cost_usd,
                    "llm_provider": response.provider,
                    "llm_model": response.model,
                },
                next_actions=[
                    {"action": "create_tasks", "tasks": all_tasks}
                ],
                confidence=0.9,
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Planner execution failed: {str(e)}",
                confidence=0.0,
            )
    
    def _validate_and_enrich_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plan structure and add task IDs."""
        if "milestones" not in plan:
            plan["milestones"] = []
        
        for milestone in plan["milestones"]:
            if "tasks" not in milestone:
                milestone["tasks"] = []
            
            for task in milestone["tasks"]:
                # Ensure required fields
                task.setdefault("priority", "medium")
                task.setdefault("dependencies", [])
                task.setdefault("estimated_effort", "2h")
                task.setdefault("tags", [])
                
                # Validate role
                role = task.get("role", "").lower()
                valid_roles = [r.value for r in AgentRole]
                if role not in valid_roles:
                    task["role"] = "backend"  # Default fallback
        
        return plan
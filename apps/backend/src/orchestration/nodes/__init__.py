"""
LangGraph nodes for each agent with real LLM execution.
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from apps.backend.src.orchestration.state import (
    WorkflowState,
    AgentOutput,
    TaskState,
    ApprovalState,
    update_task_status,
    add_agent_output,
    add_approval,
)
from apps.backend.src.agents.base import AgentRegistry, AgentRole
from apps.backend.src.core.telemetry import record_task_metrics, record_agent_metrics
from apps.backend.src.core.exceptions import AgentError
from apps.backend.src.core.tools import get_tool_executor


async def planner_node(state: WorkflowState) -> WorkflowState:
    """Planner agent node - creates or updates the project plan."""
    agent = AgentRegistry.get_agent(AgentRole.PLANNER)
    if not agent:
        raise AgentError("Planner agent not registered")
    
    current_task_id = state.get("current_task_id")
    
    if not current_task_id:
        # Initial planning
        input_data = {
            "product_request": state["input_data"].get("product_request", ""),
            "project_context": state["project_context"],
            "existing_state": {
                "completed_tasks": state["completed_tasks"],
                "artifacts": state["artifacts"],
            },
            "constraints": state["project_context"].get("constraints", {}),
        }
        
        result = await agent._run_with_tracking(
            task_id=uuid4(),
            input_data=input_data,
        )
        
        if result.success:
            plan = result.output.get("plan", {})
            tasks = result.output.get("tasks", [])
            
            # Add tasks to state
            for task_data in tasks:
                task = TaskState(
                    task_id=str(uuid4()),
                    title=task_data["title"],
                    description=task_data["description"],
                    role=task_data["role"],
                    dependencies=task_data.get("dependencies", []),
                    tags=task_data.get("tags", []),
                )
                state["tasks"].append(task)
            
            # Set first runnable task
            runnable = [t for t in state["tasks"] if not t.dependencies]
            if runnable:
                state["current_task_id"] = runnable[0].task_id
            
            output = AgentOutput(
                agent_role=AgentRole.PLANNER.value,
                task_id=str(uuid4()),
                success=True,
                output={"plan": plan, "tasks_created": len(tasks)},
                next_actions=[{"action": "execute_next_task"}],
                confidence=0.9,
            )
        else:
            output = AgentOutput(
                agent_role=AgentRole.PLANNER.value,
                task_id=str(uuid4()),
                success=False,
                error=result.error,
                confidence=0.0,
            )
    else:
        # Re-planning after task completion
        output = AgentOutput(
            agent_role=AgentRole.PLANNER.value,
            task_id=current_task_id,
            success=True,
            output={"action": "continue"},
            next_actions=[{"action": "execute_next_task"}],
            confidence=0.9,
        )
    
    add_agent_output(state, output)
    state["phase"] = "planning"
    return state


async def _execute_agent_task(
    state: WorkflowState,
    agent_role: AgentRole,
    task_data: Dict[str, Any],
) -> AgentOutput:
    """Execute a task with the specified agent."""
    agent = AgentRegistry.get_agent(agent_role)
    if not agent:
        raise AgentError(f"Agent {agent_role.value} not registered")
    
    task_id = task_data.get("task_id") or str(uuid4())
    
    # Prepare input data with context from state
    input_data = {
        "task_title": task_data.get("title", ""),
        "task_description": task_data.get("description", ""),
        "architecture": state.get("retrieved_context", {}).get("architecture", {}),
        "api_spec": state.get("retrieved_context", {}).get("api_spec", {}),
        "data_models": state.get("retrieved_context", {}).get("data_models", []),
        "tech_stack": state.get("project_context", {}).get("technology_stack", []),
        "existing_code": state.get("retrieved_context", {}).get("code", {}),
    }
    
    # Add agent-specific context
    if agent_role == AgentRole.PRODUCT_MANAGER:
        input_data["milestone_name"] = task_data.get("milestone", "")
        input_data["tasks"] = [t.__dict__ if hasattr(t, '__dict__') else t for t in state["tasks"]]
        input_data["stakeholder_requirements"] = state["input_data"].get("stakeholder_requirements", "")
    elif agent_role == AgentRole.ARCHITECT:
        input_data["user_stories"] = state.get("retrieved_context", {}).get("user_stories", [])
        input_data["requirements"] = state["input_data"]
        input_data["constraints"] = state.get("project_context", {}).get("constraints", {})
        input_data["existing_architecture"] = state.get("retrieved_context", {}).get("architecture", {})
    elif agent_role == AgentRole.BACKEND:
        input_data["task_title"] = task_data.get("title", "")
        input_data["task_description"] = task_data.get("description", "")
    elif agent_role == AgentRole.DEVOPS:
        input_data["backend_code"] = state.get("retrieved_context", {}).get("code", {})
        input_data["environment"] = state.get("project_context", {}).get("environment", "staging")
        input_data["domain"] = state.get("project_context", {}).get("domain", "agentforge.example.com")
    
    result = await agent._run_with_tracking(
        task_id=UUID(task_id) if isinstance(task_id, str) else task_id,
        input_data=input_data,
    )
    
    output = AgentOutput(
        agent_role=agent_role.value,
        task_id=task_id,
        success=result.success,
        output=result.output,
        artifacts=result.artifacts,
        next_actions=result.next_actions,
        error=result.error,
        confidence=result.confidence,
    )
    
    return output


async def product_manager_node(state: WorkflowState) -> WorkflowState:
    """Product Manager agent node."""
    output = await _execute_agent_task(state, AgentRole.PRODUCT_MANAGER, {})
    add_agent_output(state, output)
    
    # Store user stories in context
    if output.success and output.output.get("result"):
        result = output.output["result"]
        state["retrieved_context"]["user_stories"] = result.get("user_stories", [])
        state["retrieved_context"]["product_spec"] = result.get("product_spec", {})
    
    state["phase"] = "design"
    return state


async def architect_node(state: WorkflowState) -> WorkflowState:
    """Architect agent node."""
    output = await _execute_agent_task(state, AgentRole.ARCHITECT, {})
    add_agent_output(state, output)
    
    # Store architecture in context
    if output.success and output.output.get("result"):
        result = output.output["result"]
        state["retrieved_context"]["architecture"] = result.get("architecture", {})
        state["retrieved_context"]["api_design"] = result.get("api_design", {})
        state["retrieved_context"]["data_models"] = result.get("data_models", [])
        state["retrieved_context"]["adrs"] = result.get("adrs", [])
    
    state["phase"] = "design"
    return state


async def backend_node(state: WorkflowState) -> WorkflowState:
    """Backend agent node."""
    output = await _execute_agent_task(state, AgentRole.BACKEND, {})
    add_agent_output(state, output)
    
    # Store code in context
    if output.success and output.artifacts:
        code_files = {a["metadata"]["path"]: a["content"] for a in output.artifacts if a["type"] == "code"}
        state["retrieved_context"]["code"] = code_files
    
    state["phase"] = "implementation"
    return state


async def frontend_node(state: WorkflowState) -> WorkflowState:
    """Frontend agent node (placeholder - would be implemented similarly)."""
    output = await _execute_agent_task(state, AgentRole.FRONTEND, {})
    add_agent_output(state, output)
    state["phase"] = "implementation"
    return state


async def database_node(state: WorkflowState) -> WorkflowState:
    """Database agent node (placeholder)."""
    output = await _execute_agent_task(state, AgentRole.DATABASE, {})
    add_agent_output(state, output)
    state["phase"] = "implementation"
    return state


async def qa_node(state: WorkflowState) -> WorkflowState:
    """QA agent node (placeholder)."""
    output = await _execute_agent_task(state, AgentRole.QA, {})
    add_agent_output(state, output)
    state["phase"] = "testing"
    return state


async def security_node(state: WorkflowState) -> WorkflowState:
    """Security agent node (placeholder)."""
    output = await _execute_agent_task(state, AgentRole.SECURITY, {})
    add_agent_output(state, output)
    state["phase"] = "review"
    return state


async def devops_node(state: WorkflowState) -> WorkflowState:
    """DevOps agent node."""
    output = await _execute_agent_task(state, AgentRole.DEVOPS, {})
    add_agent_output(state, output)
    state["phase"] = "deployment"
    return state


async def reviewer_node(state: WorkflowState) -> WorkflowState:
    """Reviewer agent node (placeholder)."""
    output = await _execute_agent_task(state, AgentRole.REVIEWER, {})
    add_agent_output(state, output)
    state["phase"] = "review"
    return state


async def human_approval_node(state: WorkflowState) -> WorkflowState:
    """Human-in-the-loop approval node."""
    pending = state.get("pending_approvals", [])
    
    if not pending:
        state["phase"] = "planning"
        return state
    
    # In production, this would pause workflow and wait for human input
    # For now, auto-approve for demonstration
    for approval in pending:
        approval.status = "approved"
        approval.decided_by = "auto"
        approval.decided_at = datetime.utcnow()
        state["approval_history"].append(approval)
    
    state["pending_approvals"] = []
    state["phase"] = "planning"
    return state
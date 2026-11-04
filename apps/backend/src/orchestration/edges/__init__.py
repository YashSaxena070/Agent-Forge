"""
LangGraph edges for conditional routing.
"""
from typing import Dict, Any, Literal
from apps.backend.src.orchestration.state import WorkflowState
from apps.backend.src.models.entities import AgentRole


def route_to_agent(state: WorkflowState) -> Literal[
    "product_manager", "architect", "backend", "frontend", 
    "database", "qa", "security", "devops", "reviewer", 
    "human_approval", "end"
]:
    """Route to the next agent based on current task."""
    current_task_id = state.get("current_task_id")
    
    if not current_task_id:
        return "end"
    
    # Find current task
    current_task = None
    for task in state.get("tasks", []):
        if task.task_id == current_task_id:
            current_task = task
            break
    
    if not current_task:
        return "end"
    
    # Check if task is already completed
    if current_task.status == "completed":
        # Find next runnable task
        next_task = _get_next_runnable_task(state)
        if next_task:
            state["current_task_id"] = next_task.task_id
            return _role_to_node(next_task.role)
        return "end"
    
    # Check if task needs human approval
    if current_task.status == "approval_required":
        return "human_approval"
    
    # Route to appropriate agent
    return _role_to_node(current_task.role)


def _get_next_runnable_task(state: WorkflowState) -> Dict[str, Any] | None:
    """Get the next runnable task (dependencies satisfied)."""
    completed_task_ids = set(state.get("completed_tasks", []))
    
    for task in state.get("tasks", []):
        if task.status != "pending":
            continue
        
        # Check if all dependencies are completed
        deps_satisfied = all(dep_id in completed_task_ids for dep_id in task.dependencies)
        
        if deps_satisfied:
            return task
    
    return None


def _role_to_node(role: str) -> str:
    """Map agent role to node name."""
    role_mapping = {
        AgentRole.PRODUCT_MANAGER.value: "product_manager",
        AgentRole.ARCHITECT.value: "architect",
        AgentRole.BACKEND.value: "backend",
        AgentRole.FRONTEND.value: "frontend",
        AgentRole.DATABASE.value: "database",
        AgentRole.QA.value: "qa",
        AgentRole.SECURITY.value: "security",
        AgentRole.DEVOPS.value: "devops",
        AgentRole.REVIEWER.value: "reviewer",
    }
    return role_mapping.get(role, "end")


def should_continue(state: WorkflowState) -> Literal["continue", "human_approval", "end"]:
    """Determine if workflow should continue to next task."""
    # Check for pending approvals
    if state.get("pending_approvals"):
        return "human_approval"
    
    # Check if there are more runnable tasks
    next_task = _get_next_runnable_task(state)
    if next_task:
        state["current_task_id"] = next_task.task_id
        return "continue"
    
    # Check if all tasks are completed
    all_completed = all(t.status == "completed" for t in state.get("tasks", []))
    if all_completed:
        return "end"
    
    # Check for failed tasks
    failed_tasks = [t for t in state.get("tasks", []) if t.status == "failed"]
    if failed_tasks:
        # Could implement retry logic here
        return "end"
    
    return "end"


def check_approval(state: WorkflowState) -> Literal["approved", "rejected", "continue"]:
    """Check approval status and route accordingly."""
    # In a real implementation, this would check the actual approval status
    # For now, we'll check the most recent approval
    
    approval_history = state.get("approval_history", [])
    
    if not approval_history:
        return "continue"
    
    last_approval = approval_history[-1]
    
    if last_approval.status == "approved":
        return "approved"
    elif last_approval.status == "rejected":
        return "rejected"
    
    return "continue"
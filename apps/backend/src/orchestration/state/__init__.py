"""
Workflow state definition for LangGraph.
"""
from typing import Dict, Any, List, Optional, Annotated
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field
from langgraph.graph import add_messages
from typing_extensions import TypedDict


class AgentOutput(BaseModel):
    """Output from an agent execution."""
    agent_role: str
    task_id: str
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    next_actions: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskState(BaseModel):
    """State of a single task."""
    task_id: str
    title: str
    description: str
    role: str
    status: str = "pending"
    dependencies: List[str] = Field(default_factory=list)
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    assigned_agent: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ApprovalState(BaseModel):
    """State of an approval request."""
    approval_id: str
    workflow_id: str
    task_id: str
    title: str
    description: str
    options: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "pending"
    requested_by: str
    decided_by: Optional[str] = None
    selected_option: Optional[str] = None
    comments: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None


class WorkflowState(TypedDict):
    """Main workflow state for LangGraph."""
    # Workflow identification
    workflow_id: str
    user_id: str
    project_id: str
    
    # Execution state
    phase: str
    status: str
    progress: int
    
    # Input and context
    input_data: Dict[str, Any]
    project_context: Dict[str, Any]
    retrieved_context: Dict[str, Any]
    
    # Task management
    tasks: Annotated[List[TaskState], add_messages]
    completed_tasks: List[str]
    failed_tasks: List[str]
    current_task_id: Optional[str]
    
    # Agent outputs
    agent_outputs: Annotated[List[AgentOutput], add_messages]
    
    # Approvals
    pending_approvals: List[ApprovalState]
    approval_history: List[ApprovalState]
    
    # Artifacts
    artifacts: List[Dict[str, Any]]
    
    # Errors and retries
    errors: List[Dict[str, Any]]
    retry_count: Dict[str, int]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metadata: Dict[str, Any]


def create_initial_state(
    workflow_id: UUID,
    user_id: UUID,
    input_data: Dict[str, Any],
    project_id: Optional[UUID] = None,
    project_context: Optional[Dict[str, Any]] = None,
) -> WorkflowState:
    """Create initial workflow state."""
    now = datetime.utcnow()
    
    return WorkflowState(
        workflow_id=str(workflow_id),
        user_id=str(user_id),
        project_id=str(project_id) if project_id else "",
        phase="planning",
        status="running",
        progress=0,
        input_data=input_data,
        project_context=project_context or {},
        retrieved_context={},
        tasks=[],
        completed_tasks=[],
        failed_tasks=[],
        current_task_id=None,
        agent_outputs=[],
        pending_approvals=[],
        approval_history=[],
        artifacts=[],
        errors=[],
        retry_count={},
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=None,
        metadata={},
    )


def update_state_timestamp(state: WorkflowState) -> WorkflowState:
    """Update the timestamp in state."""
    state["updated_at"] = datetime.utcnow()
    return state


def add_agent_output(state: WorkflowState, output: AgentOutput) -> WorkflowState:
    """Add agent output to state."""
    state["agent_outputs"].append(output)
    return update_state_timestamp(state)


def add_task(state: WorkflowState, task: TaskState) -> WorkflowState:
    """Add task to state."""
    state["tasks"].append(task)
    return update_state_timestamp(state)


def update_task_status(
    state: WorkflowState,
    task_id: str,
    status: str,
    progress: int = None,
    result: Dict[str, Any] = None,
    error: str = None,
) -> WorkflowState:
    """Update task status in state."""
    for task in state["tasks"]:
        if task.task_id == task_id:
            task.status = status
            if progress is not None:
                task.progress = progress
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            if status == "running" and not task.started_at:
                task.started_at = datetime.utcnow()
            if status in ("completed", "failed"):
                task.completed_at = datetime.utcnow()
            break
    return update_state_timestamp(state)


def add_approval(state: WorkflowState, approval: ApprovalState) -> WorkflowState:
    """Add approval request to state."""
    state["pending_approvals"].append(approval)
    return update_state_timestamp(state)


def resolve_approval(
    state: WorkflowState,
    approval_id: str,
    approved: bool,
    decided_by: str,
    selected_option: str = None,
    comments: str = None,
) -> WorkflowState:
    """Resolve an approval request."""
    for approval in state["pending_approvals"]:
        if approval.approval_id == approval_id:
            approval.status = "approved" if approved else "rejected"
            approval.decided_by = decided_by
            approval.selected_option = selected_option
            approval.comments = comments
            approval.decided_at = datetime.utcnow()
            state["approval_history"].append(approval)
            state["pending_approvals"].remove(approval)
            break
    return update_state_timestamp(state)
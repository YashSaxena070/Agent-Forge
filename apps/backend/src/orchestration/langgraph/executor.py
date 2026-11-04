"""
LangGraph workflow orchestration.
"""
from typing import Dict, Any, List, Optional, Callable
from uuid import UUID
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from apps.backend.src.orchestration.state import WorkflowState, create_initial_state
from apps.backend.src.orchestration.nodes import (
    planner_node,
    product_manager_node,
    architect_node,
    backend_node,
    frontend_node,
    database_node,
    qa_node,
    security_node,
    devops_node,
    reviewer_node,
    human_approval_node,
)
from apps.backend.src.orchestration.edges import (
    should_continue,
    route_to_agent,
    check_approval,
)
from apps.backend.src.core.telemetry import get_tracer


tracer = get_tracer("agentforge.orchestration")


def create_workflow_graph() -> StateGraph:
    """Create the main workflow StateGraph."""
    
    # Define the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes for each agent
    workflow.add_node("planner", planner_node)
    workflow.add_node("product_manager", product_manager_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("backend", backend_node)
    workflow.add_node("frontend", frontend_node)
    workflow.add_node("database", database_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("security", security_node)
    workflow.add_node("devops", devops_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("human_approval", human_approval_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "planner",
        route_to_agent,
        {
            "product_manager": "product_manager",
            "architect": "architect",
            "backend": "backend",
            "frontend": "frontend",
            "database": "database",
            "qa": "qa",
            "security": "security",
            "devops": "devops",
            "reviewer": "reviewer",
            "human_approval": "human_approval",
            "end": END,
        }
    )
    
    # Each agent routes to next agent or human approval
    for agent in ["product_manager", "architect", "backend", "frontend", 
                   "database", "qa", "security", "devops", "reviewer"]:
        workflow.add_conditional_edges(
            agent,
            should_continue,
            {
                "continue": "planner",  # Go back to planner for next task
                "human_approval": "human_approval",
                "end": END,
            }
        )
    
    # Human approval routes back to planner or ends
    workflow.add_conditional_edges(
        "human_approval",
        check_approval,
        {
            "approved": "planner",
            "rejected": END,
            "continue": "planner",
        }
    )
    
    return workflow


class WorkflowExecutor:
    """Executes LangGraph workflows with checkpointing."""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.graph = create_workflow_graph()
        self.checkpointer = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.checkpointer)
    
    async def execute_workflow(
        self,
        workflow_id: UUID,
        user_id: UUID,
        initial_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a workflow from start to finish."""
        from apps.backend.src.services.workflow import WorkflowService
        from apps.backend.src.models.entities import WorkflowStatus, WorkflowPhase
        
        workflow_service = WorkflowService(self.db_session)
        
        # Update workflow status
        await workflow_service.set_workflow_status(
            workflow_id,
            WorkflowStatus.RUNNING,
            WorkflowPhase.PLANNING,
        )
        
        # Create initial state
        initial_state = create_initial_state(
            workflow_id=workflow_id,
            user_id=user_id,
            input_data=initial_input,
        )
        
        # Configure thread for checkpointing
        config = {"configurable": {"thread_id": str(workflow_id)}}
        
        try:
            # Execute workflow
            final_state = await self.app.ainvoke(initial_state, config=config)
            
            # Update workflow with final state
            await workflow_service.update_workflow_state(workflow_id, final_state)
            
            # Mark as completed
            await workflow_service.set_workflow_status(
                workflow_id,
                WorkflowStatus.COMPLETED,
                WorkflowPhase.MONITORING,
                progress=100,
            )
            
            return final_state
            
        except Exception as e:
            # Mark as failed
            await workflow_service.set_workflow_status(
                workflow_id,
                WorkflowStatus.FAILED,
                error=str(e),
            )
            raise
    
    async def resume_workflow(
        self,
        workflow_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Resume a paused workflow from checkpoint."""
        from apps.backend.src.services.workflow import WorkflowService
        from apps.backend.src.models.entities import WorkflowStatus, WorkflowPhase
        
        workflow_service = WorkflowService(self.db_session)
        
        # Update workflow status
        await workflow_service.set_workflow_status(
            workflow_id,
            WorkflowStatus.RUNNING,
        )
        
        config = {"configurable": {"thread_id": str(workflow_id)}}
        
        try:
            # Resume from checkpoint
            final_state = await self.app.ainvoke(None, config=config)
            
            await workflow_service.update_workflow_state(workflow_id, final_state)
            
            await workflow_service.set_workflow_status(
                workflow_id,
                WorkflowStatus.COMPLETED,
                WorkflowPhase.MONITORING,
                progress=100,
            )
            
            return final_state
            
        except Exception as e:
            await workflow_service.set_workflow_status(
                workflow_id,
                WorkflowStatus.FAILED,
                error=str(e),
            )
            raise
    
    async def get_workflow_state(self, workflow_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current workflow state from checkpoint."""
        config = {"configurable": {"thread_id": str(workflow_id)}}
        try:
            state = await self.app.aget_state(config)
            return state.values if state else None
        except Exception:
            return None


# Global executor instance
_executor: Optional[WorkflowExecutor] = None


def get_workflow_executor(db_session=None) -> WorkflowExecutor:
    """Get or create workflow executor."""
    global _executor
    if _executor is None:
        _executor = WorkflowExecutor(db_session)
    return _executor
"""
Workflow service for managing workflow operations.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.models.entities import Workflow, Project, Task, WorkflowStatus, WorkflowPhase
from apps.backend.src.core.exceptions import NotFoundError, WorkflowError


class WorkflowService:
    """Service for workflow operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_workflow(
        self,
        project_id: UUID,
        name: str,
        description: str,
        initial_state: dict,
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            project_id=project_id,
            name=name,
            description=description,
            initial_state=initial_state,
            state=initial_state.copy(),
        )
        
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)
        
        return workflow
    
    async def get_workflow(self, workflow_id: UUID) -> Optional[Workflow]:
        """Get workflow by ID."""
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()
    
    async def update_workflow_state(
        self,
        workflow_id: UUID,
        state_update: dict,
    ) -> Workflow:
        """Update workflow state."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise NotFoundError("Workflow", workflow_id)
        
        workflow.state.update(state_update)
        workflow.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(workflow)
        
        return workflow
    
    async def set_workflow_status(
        self,
        workflow_id: UUID,
        status: WorkflowStatus,
        phase: Optional[WorkflowPhase] = None,
        progress: Optional[int] = None,
        error: Optional[str] = None,
    ) -> Workflow:
        """Set workflow status."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise NotFoundError("Workflow", workflow_id)
        
        workflow.status = status
        if phase:
            workflow.current_phase = phase
        if progress is not None:
            workflow.progress = progress
        if error:
            workflow.error = error
        
        if status == WorkflowStatus.RUNNING and not workflow.started_at:
            workflow.started_at = datetime.utcnow()
        elif status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            workflow.completed_at = datetime.utcnow()
            if workflow.started_at:
                workflow.duration_seconds = (workflow.completed_at - workflow.started_at).total_seconds()
        
        await self.db.commit()
        await self.db.refresh(workflow)
        
        return workflow
    
    async def pause_workflow(self, workflow_id: UUID) -> Workflow:
        """Pause a running workflow."""
        return await self.set_workflow_status(workflow_id, WorkflowStatus.PAUSED)
    
    async def resume_workflow(self, workflow_id: UUID) -> Workflow:
        """Resume a paused workflow."""
        return await self.set_workflow_status(workflow_id, WorkflowStatus.RUNNING)
    
    async def cancel_workflow(self, workflow_id: UUID) -> Workflow:
        """Cancel a workflow."""
        return await self.set_workflow_status(workflow_id, WorkflowStatus.CANCELLED)
    
    async def create_tasks_from_plan(
        self,
        workflow_id: UUID,
        tasks_data: List[dict],
    ) -> List[Task]:
        """Create tasks from planner output."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise NotFoundError("Workflow", workflow_id)
        
        tasks = []
        for task_data in tasks_data:
            task = Task(
                title=task_data["title"],
                description=task_data["description"],
                role=task_data["role"],
                priority=task_data.get("priority", "medium"),
                dependencies=[UUID(d) for d in task_data.get("dependencies", [])],
                estimated_effort=task_data.get("estimated_effort"),
                tags=task_data.get("tags", []),
                project_id=workflow.project_id,
                workflow_id=workflow_id,
            )
            tasks.append(task)
            self.db.add(task)
        
        await self.db.commit()
        
        for task in tasks:
            await self.db.refresh(task)
        
        return tasks
    
    async def get_next_runnable_tasks(self, workflow_id: UUID) -> List[Task]:
        """Get tasks that are ready to run (dependencies satisfied)."""
        result = await self.db.execute(
            select(Task).where(
                Task.workflow_id == workflow_id,
                Task.status == TaskStatus.PENDING,
            )
        )
        pending_tasks = result.scalars().all()
        
        runnable = []
        for task in pending_tasks:
            deps_satisfied = True
            for dep_id in task.dependencies:
                dep_result = await self.db.execute(
                    select(Task).where(Task.id == dep_id)
                )
                dep_task = dep_result.scalar_one_or_none()
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    deps_satisfied = False
                    break
            
            if deps_satisfied:
                runnable.append(task)
        
        return runnable
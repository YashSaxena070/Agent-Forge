"""
Deployment service for managing deployments.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.models.entities import Deployment, Project, Workflow, DeploymentStatus, DeploymentStrategy, Artifact
from apps.backend.src.core.exceptions import NotFoundError, DeploymentError
from apps.backend.src.integrations.kubernetes.client import KubernetesClient
from apps.backend.src.integrations.docker.client import DockerClient


class DeploymentService:
    """Service for deployment operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.k8s_client = KubernetesClient()
        self.docker_client = DockerClient()
    
    async def create_deployment(
        self,
        project_id: UUID,
        workflow_id: UUID,
        environment: str,
        strategy: DeploymentStrategy,
        config: dict,
        triggered_by: UUID,
    ) -> Deployment:
        """Create a new deployment."""
        # Generate version
        version = f"v{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        deployment = Deployment(
            project_id=project_id,
            workflow_id=workflow_id,
            environment=environment,
            strategy=strategy,
            config=config,
            version=version,
            triggered_by=triggered_by,
        )
        
        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)
        
        return deployment
    
    async def execute_deployment(self, deployment_id: UUID) -> Deployment:
        """Execute a deployment."""
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()
        
        if not deployment:
            raise NotFoundError("Deployment", deployment_id)
        
        if deployment.status == DeploymentStatus.RUNNING:
            raise DeploymentError("Deployment is already running")
        
        deployment.status = DeploymentStatus.RUNNING
        deployment.started_at = datetime.utcnow()
        deployment.logs = ["Deployment started"]
        
        await self.db.commit()
        
        try:
            # Execute based on strategy
            if deployment.strategy == DeploymentStrategy.ROLLING:
                await self._execute_rolling_deployment(deployment)
            elif deployment.strategy == DeploymentStrategy.BLUE_GREEN:
                await self._execute_blue_green_deployment(deployment)
            elif deployment.strategy == DeploymentStrategy.CANARY:
                await self._execute_canary_deployment(deployment)
            else:
                await self._execute_recreate_deployment(deployment)
            
            deployment.status = DeploymentStatus.COMPLETED
            deployment.logs.append("Deployment completed successfully")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error = str(e)
            deployment.logs.append(f"Deployment failed: {str(e)}")
            raise DeploymentError(f"Deployment failed: {str(e)}")
        
        finally:
            deployment.completed_at = datetime.utcnow()
            if deployment.started_at:
                deployment.duration_seconds = (deployment.completed_at - deployment.started_at).total_seconds()
            await self.db.commit()
            await self.db.refresh(deployment)
        
        return deployment
    
    async def _execute_rolling_deployment(self, deployment: Deployment):
        """Execute rolling deployment."""
        deployment.logs.append("Starting rolling deployment")
        
        # Build and push Docker images
        deployment.logs.append("Building Docker images")
        # await self.docker_client.build_and_push(deployment.config)
        
        # Apply Kubernetes manifests
        deployment.logs.append("Applying Kubernetes manifests")
        # await self.k8s_client.apply_manifests(deployment.config, deployment.environment)
        
        # Wait for rollout
        deployment.logs.append("Waiting for rollout to complete")
        # await self.k8s_client.wait_for_rollout(deployment.config, deployment.environment)
        
        deployment.logs.append("Rolling deployment completed")
    
    async def _execute_blue_green_deployment(self, deployment: Deployment):
        """Execute blue-green deployment."""
        deployment.logs.append("Starting blue-green deployment")
        # Implementation would go here
        deployment.logs.append("Blue-green deployment completed")
    
    async def _execute_canary_deployment(self, deployment: Deployment):
        """Execute canary deployment."""
        deployment.logs.append("Starting canary deployment")
        # Implementation would go here
        deployment.logs.append("Canary deployment completed")
    
    async def _execute_recreate_deployment(self, deployment: Deployment):
        """Execute recreate deployment."""
        deployment.logs.append("Starting recreate deployment")
        # Implementation would go here
        deployment.logs.append("Recreate deployment completed")
    
    async def rollback_deployment(self, deployment_id: UUID, target_version: Optional[str] = None) -> Deployment:
        """Rollback a deployment."""
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()
        
        if not deployment:
            raise NotFoundError("Deployment", deployment_id)
        
        if deployment.status not in (DeploymentStatus.COMPLETED, DeploymentStatus.FAILED):
            raise DeploymentError("Can only rollback completed or failed deployments")
        
        deployment.status = DeploymentStatus.RUNNING
        deployment.started_at = datetime.utcnow()
        deployment.logs.append(f"Rollback started to version {target_version or deployment.rollback_version}")
        
        await self.db.commit()
        
        try:
            # Perform rollback
            deployment.logs.append("Rolling back Kubernetes resources")
            # await self.k8s_client.rollback(deployment.config, deployment.environment, target_version)
            
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.logs.append("Rollback completed")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error = f"Rollback failed: {str(e)}"
            deployment.logs.append(f"Rollback failed: {str(e)}")
            raise DeploymentError(f"Rollback failed: {str(e)}")
        
        finally:
            deployment.completed_at = datetime.utcnow()
            if deployment.started_at:
                deployment.duration_seconds = (deployment.completed_at - deployment.started_at).total_seconds()
            await self.db.commit()
            await self.db.refresh(deployment)
        
        return deployment
    
    async def get_deployment(self, deployment_id: UUID) -> Optional[Deployment]:
        """Get deployment by ID."""
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        return result.scalar_one_or_none()
    
    async def list_deployments(
        self,
        project_id: UUID = None,
        environment: str = None,
        status: DeploymentStatus = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Deployment]:
        """List deployments with filters."""
        query = select(Deployment)
        
        if project_id:
            query = query.where(Deployment.project_id == project_id)
        if environment:
            query = query.where(Deployment.environment == environment)
        if status:
            query = query.where(Deployment.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Deployment.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
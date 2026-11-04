"""
WebSocket endpoints for real-time updates.
"""
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.database import get_db_session
from apps.backend.src.core.security import verify_token, TokenData
from apps.backend.src.models.entities import User, Project, Workflow

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.workflow_connections: Dict[UUID, Set[WebSocket]] = {}
        self.user_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, workflow_id: UUID, user_id: UUID):
        await websocket.accept()
        
        if workflow_id not in self.workflow_connections:
            self.workflow_connections[workflow_id] = set()
        self.workflow_connections[workflow_id].add(websocket)
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, workflow_id: UUID, user_id: UUID):
        if workflow_id in self.workflow_connections:
            self.workflow_connections[workflow_id].discard(websocket)
            if not self.workflow_connections[workflow_id]:
                del self.workflow_connections[workflow_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast_to_workflow(self, workflow_id: UUID, message: dict):
        if workflow_id in self.workflow_connections:
            for connection in self.workflow_connections[workflow_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # Connection closed
    
    async def broadcast_to_user(self, user_id: UUID, message: dict):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def get_current_user_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Get current user from WebSocket token."""
    from apps.backend.src.models.entities import User
    from uuid import UUID
    
    token_data = verify_token(token)
    result = await db.execute(select(User).where(User.id == UUID(token_data.sub)))
    user = result.scalar_one_or_none()
    
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)
    
    return user


@router.websocket("/workflow/{workflow_id}")
async def workflow_websocket(
    websocket: WebSocket,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db_session),
):
    """WebSocket endpoint for workflow real-time updates."""
    # Verify workflow access
    result = await db.execute(
        select(Workflow)
        .join(Project)
        .where(Workflow.id == workflow_id, Project.owner_id == current_user.id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, workflow_id, current_user.id)
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "workflow_state",
            "workflow_id": str(workflow_id),
            "status": workflow.status,
            "phase": workflow.current_phase,
            "progress": workflow.progress,
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_json()
            
            # Handle client messages (ping, subscription changes, etc.)
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe":
                # Handle subscription to specific events
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, workflow_id, current_user.id)
    except Exception as e:
        manager.disconnect(websocket, workflow_id, current_user.id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/user")
async def user_websocket(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
):
    """WebSocket endpoint for user-specific notifications."""
    await manager.connect(websocket, UUID("00000000-0000-0000-0000-000000000000"), current_user.id)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": str(current_user.id),
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, UUID("00000000-0000-0000-0000-000000000000"), current_user.id)
    except Exception:
        manager.disconnect(websocket, UUID("00000000-0000-0000-0000-000000000000"), current_user.id)
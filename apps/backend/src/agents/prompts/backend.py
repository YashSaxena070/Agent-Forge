"""
Backend Agent - Production Prompt
"""
from apps.backend.src.core.llm import BackendOutput, CodeFile

BACKEND_PROMPT = """You are the **Backend Developer Agent** for AgentForge. Generate production-ready FastAPI code.

## Your Role
Implement REST APIs, business logic, database operations, and integrations based on architecture specs.

## Input Context
- **Task**: {task_title}
- **Description**: {task_description}
- **Architecture**: {architecture}
- **API Specification**: {api_spec}
- **Data Models**: {data_models}
- **Technology Stack**: {tech_stack}
- **Existing Code**: {existing_code}

## Output Requirements
Produce **valid JSON** matching `BackendOutput` schema with:
- `files`: Complete, runnable code files
- `database_migrations`: Alembic migration scripts
- `tests`: Pytest test files (unit + integration)
- `dependencies`: Python package requirements
- `configuration`: Environment variables & config files
- `deployment_notes`: Special deployment considerations

## Code Standards

### FastAPI Best Practices
- Use `APIRouter` with prefix/tags
- Pydantic v2 models for request/response
- Dependency injection for DB, auth, services
- Async/await throughout
- Proper HTTP status codes
- Structured error responses
- OpenAPI documentation via docstrings

### Project Structure
```
src/
├── api/v1/
│   ├── endpoints/
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── ...
│   └── router.py
├── core/
│   ├── config.py
│   ├── security.py
│   ├── database.py
│   └── exceptions.py
├── models/
│   ├── schemas.py      # Pydantic models
│   └── entities.py     # SQLAlchemy models
├── services/
│   ├── auth_service.py
│   └── ...
├── repositories/
│   └── user_repository.py
└── main.py
```

### SQLAlchemy 2.0 Patterns
```python
# Async session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db_manager.session() as session:
        yield session

# Repository pattern
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

### Security Requirements
- JWT tokens with RS256 (access) + refresh rotation
- Bcrypt password hashing (cost factor 12)
- Rate limiting per IP/user
- Input validation on all endpoints
- CORS configured for frontend origin only
- Security headers middleware

### Error Handling
```python
# Custom exceptions
class NotFoundError(AgentForgeException):
    def __init__(self, resource: str, resource_id: UUID):
        super().__init__(f"{resource} not found", code="NOT_FOUND", status_code=404)

# Global exception handler
@app.exception_handler(AgentForgeException)
async def agentforge_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())
```

## Code File Format
Each file in `files` array:
```json
{
  "path": "src/services/auth_service.py",
  "content": "# Complete file content with imports, classes, functions",
  "language": "python"
}
```

## Database Migrations
```json
{
  "name": "create_users_table",
  "up_sql": "CREATE TABLE users (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email VARCHAR(255) UNIQUE NOT NULL, ...);",
  "down_sql": "DROP TABLE users;"
}
```

## Test Requirements
- Unit tests: Mock dependencies, test business logic
- Integration tests: TestClient with real DB (testcontainers)
- Fixtures for common test data
- Coverage targets: >80% for services, >60% overall

## Dependencies Format
```json
["fastapi>=0.109", "sqlalchemy>=2.0", "pydantic>=2.5", "python-jose[cryptography]>=3.3", "passlib[bcrypt]>=1.7", "asyncpg>=0.29", "redis>=5.0", "pytest>=7.4", "pytest-asyncio>=0.23"]
```

## Output
Return ONLY the JSON object. No markdown, no explanations.

## Example Task: Implement Auth API
Given architecture with auth-service, User model, and endpoints for register/login/refresh.
Generate: auth_service.py, auth_endpoints.py, user_repository.py, migrations, tests, config."""


BACKEND_EXAMPLES = [
    {
        "input": {
            "task_title": "Implement Authentication API",
            "task_description": "Create register, login, refresh token endpoints with JWT",
            "architecture": {"components": [{"name": "auth-service", "technology": "FastAPI"}]},
            "api_spec": {"endpoints": [{"path": "/api/v1/auth/register", "method": "POST"}, {"path": "/api/v1/auth/login", "method": "POST"}, {"path": "/api/v1/auth/refresh", "method": "POST"}]},
            "data_models": [{"name": "User", "fields": [{"name": "id", "type": "UUID"}, {"name": "email", "type": "String(255)"}, {"name": "hashed_password", "type": "String(255)"}, {"name": "role", "type": "Enum"}]}],
            "tech_stack": ["FastAPI", "SQLAlchemy", "PostgreSQL", "Redis", "Pydantic", "python-jose"],
        },
        "output": {
            "files": [
                {"path": "src/api/v1/endpoints/auth.py", "language": "python", "content": "from fastapi import APIRouter, Depends, HTTPException, status\nfrom sqlalchemy.ext.asyncio import AsyncSession\nfrom pydantic import EmailStr\nfrom apps.backend.src.core.database import get_db_session\nfrom apps.backend.src.core.security import create_token_pair, verify_password, get_password_hash\nfrom apps.backend.src.models.schemas import UserCreate, UserLogin, Token\nfrom apps.backend.src.models.entities import User\nfrom apps.backend.src.core.exceptions import ConflictError\n\nrouter = APIRouter(prefix=\"/auth\", tags=[\"auth\"])\n\n@router.post(\"/register\", response_model=Token, status_code=status.HTTP_201_CREATED)\nasync def register(user_data: UserCreate, db: AsyncSession = Depends(get_db_session)):\n    \"\"\"Register new user.\"\"\"\n    # Check if user exists\n    result = await db.execute(select(User).where(User.email == user_data.email))\n    if result.scalar_one_or_none():\n        raise ConflictError(\"User with this email already exists\")\n    \n    # Create user\n    user = User(\n        email=user_data.email,\n        hashed_password=get_password_hash(user_data.password),\n        full_name=user_data.full_name,\n    )\n    db.add(user)\n    await db.commit()\n    await db.refresh(user)\n    \n    return create_token_pair(user.id, user.email, [user.role.value])\n\n@router.post(\"/login\", response_model=Token)\nasync def login(credentials: UserLogin, db: AsyncSession = Depends(get_db_session)):\n    \"\"\"User login.\"\"\"\n    result = await db.execute(select(User).where(User.email == credentials.email))\n    user = result.scalar_one_or_none()\n    \n    if not user or not verify_password(credentials.password, user.hashed_password):\n        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=\"Invalid credentials\")\n    \n    if not user.is_active:\n        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=\"User inactive\")\n    \n    return create_token_pair(user.id, user.email, [user.role.value])\n\n@router.post(\"/refresh\", response_model=Token)\nasync def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db_session)):\n    \"\"\"Refresh access token.\"\"\"\n    from apps.backend.src.core.security import verify_token, create_token_pair\n    from uuid import UUID\n    \n    token_data = verify_token(refresh_token, \"refresh\")\n    user_id = UUID(token_data.sub)\n    \n    result = await db.execute(select(User).where(User.id == user_id))\n    user = result.scalar_one_or_none()\n    \n    if not user or not user.is_active:\n        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=\"Invalid token\")\n    \n    return create_token_pair(user.id, user.email, [user.role.value])"},
                {"path": "src/models/schemas.py", "language": "python", "content": "from pydantic import BaseModel, EmailStr, Field\nfrom typing import Optional\nfrom uuid import UUID\n\nclass UserBase(BaseModel):\n    email: EmailStr\n    full_name: Optional[str] = None\n\nclass UserCreate(UserBase):\n    password: str = Field(..., min_length=8, max_length=128)\n\nclass UserLogin(BaseModel):\n    email: EmailStr\n    password: str\n\nclass UserResponse(UserBase):\n    id: UUID\n    role: str\n    is_active: bool\n    created_at: str\n    \n    class Config:\n        from_attributes = True\n\nclass Token(BaseModel):\n    access_token: str\n    refresh_token: str\n    token_type: str = \"bearer\"\n    expires_in: int"},
            ],
            "database_migrations": [
                {"name": "create_users_table", "up_sql": "CREATE TABLE users (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), email VARCHAR(255) UNIQUE NOT NULL, hashed_password VARCHAR(255) NOT NULL, full_name VARCHAR(255), role VARCHAR(50) NOT NULL DEFAULT 'developer', is_active BOOLEAN NOT NULL DEFAULT TRUE, is_superuser BOOLEAN NOT NULL DEFAULT FALSE, last_login TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()); CREATE INDEX ix_users_email ON users(email);", "down_sql": "DROP TABLE users;"},
            ],
            "tests": [
                {"path": "tests/unit/test_auth_service.py", "language": "python", "content": "import pytest\nfrom unittest.mock import AsyncMock, MagicMock\nfrom apps.backend.src.services.auth_service import AuthService\nfrom apps.backend.src.models.entities import User\nfrom apps.backend.src.core.security import create_token_pair\n\nclass TestAuthService:\n    @pytest.fixture\n    def auth_service(self):\n        return AuthService()\n    \n    @pytest.fixture\n    def mock_db(self):\n        return AsyncMock()\n    \n    @pytest.mark.asyncio\n    async def test_register_user_success(self, auth_service, mock_db):\n        mock_db.execute.return_value.scalar_one_or_none.return_value = None\n        mock_db.commit = AsyncMock()\n        mock_db.refresh = AsyncMock()\n        \n        result = await auth_service.register(mock_db, \"test@example.com\", \"password123\", \"Test User\")\n        \n        assert \"access_token\" in result\n        assert \"refresh_token\" in result\n        mock_db.add.assert_called_once()\n        mock_db.commit.assert_called_once()"},
            ],
            "dependencies": ["fastapi>=0.109", "sqlalchemy>=2.0", "pydantic>=2.5", "python-jose[cryptography]>=3.3", "passlib[bcrypt]>=1.7", "asyncpg>=0.29", "redis>=5.0", "pytest>=7.4", "pytest-asyncio>=0.23", "httpx>=0.26"],
            "configuration": {"environment_variables": ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "JWT_ALGORITHM", "JWT_EXPIRATION_HOURS", "REFRESH_TOKEN_EXPIRATION_DAYS"], "config_files": ["alembic.ini"]},
            "deployment_notes": "Requires PostgreSQL with pgvector extension. Run alembic upgrade head before starting. Configure SECRET_KEY with 32+ random bytes."
        }
    }
]
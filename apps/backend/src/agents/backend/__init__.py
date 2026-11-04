"""
Backend Agent with real LLM integration and code generation.
"""
import json
import re
from typing import Any, Dict, List
from uuid import UUID

from apps.backend.src.agents.base import BaseAgent, AgentResult, agent_role
from apps.backend.src.agents.prompts import BACKEND_PROMPT
from apps.backend.src.core.llm import LLMProviderFactory, BackendOutput, CodeFile
from apps.backend.src.models.entities import AgentRole
from apps.backend.src.core.tools import get_tool_executor
from apps.backend.src.core.telemetry import record_agent_metrics


@agent_role(AgentRole.BACKEND)
class BackendAgent(BaseAgent):
    """Backend Agent - Generates production FastAPI code with real LLM."""
    
    role = AgentRole.BACKEND
    name = "Backend Developer"
    description = "Implements REST/gRPC APIs, business logic, database operations, authentication, and integrations"
    capabilities = [
        "api_implementation",
        "business_logic",
        "database_operations",
        "authentication_authorization",
        "third_party_integrations",
        "performance_optimization",
        "error_handling",
    ]
    
    async def execute(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        db_session=None,
    ) -> AgentResult:
        """Execute the backend agent with real LLM."""
        task_title = input_data.get("task_title", "")
        task_description = input_data.get("task_description", "")
        architecture = input_data.get("architecture", {})
        api_spec = input_data.get("api_spec", {})
        data_models = input_data.get("data_models", [])
        tech_stack = input_data.get("tech_stack", {})
        existing_code = input_data.get("existing_code", {})
        
        messages = [
            {"role": "system", "content": "You are an expert backend developer. Output valid JSON only with complete, production-ready code."},
            {"role": "user", "content": BACKEND_PROMPT.format(
                task_title=task_title,
                task_description=task_description,
                architecture=json.dumps(architecture, indent=2),
                api_spec=json.dumps(api_spec, indent=2),
                data_models=json.dumps(data_models, indent=2),
                tech_stack=json.dumps(tech_stack, indent=2),
                existing_code=json.dumps(existing_code, indent=2),
            )},
        ]
        
        try:
            response = await LLMProviderFactory.complete(
                messages=messages,
                response_model=BackendOutput,
                agent_role="backend",
                temperature=0.1,
                max_tokens=16000,  # Large context for code generation
            )
            
            if not response.parsed:
                return AgentResult(
                    success=False,
                    error="Failed to parse backend output",
                    confidence=0.0,
                )
            
            backend_output = response.parsed.model_dump()
            
            # Post-process and validate generated code
            processed_files = self._process_generated_files(backend_output.get("files", []))
            processed_tests = self._process_generated_files(backend_output.get("tests", []))
            processed_migrations = backend_output.get("database_migrations", [])
            
            artifacts = []
            for f in processed_files:
                artifacts.append({
                    "name": f["path"].split("/")[-1],
                    "type": "code",
                    "content": f["content"],
                    "metadata": {"path": f["path"], "language": f.get("language", "python")},
                })
            
            for f in processed_tests:
                artifacts.append({
                    "name": f["path"].split("/")[-1],
                    "type": "test",
                    "content": f["content"],
                    "metadata": {"path": f["path"], "language": f.get("language", "python")},
                })
            
            for migration in processed_migrations:
                artifacts.append({
                    "name": f"{migration['name']}.sql",
                    "type": "code",
                    "content": migration["up_sql"],
                    "metadata": {"type": "migration", "down_sql": migration.get("down_sql", "")},
                })
            
            return AgentResult(
                success=True,
                output={
                    "result": backend_output,
                    "tokens_used": response.tokens_used,
                    "cost_usd": response.cost_usd,
                    "llm_provider": response.provider,
                    "llm_model": response.model,
                },
                artifacts=artifacts,
                next_actions=[
                    {"action": "run_tests", "test_files": [f["path"] for f in processed_tests]}
                ],
                confidence=0.85,
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Backend execution failed: {str(e)}",
                confidence=0.0,
            )
    
    def _process_generated_files(self, files: List[Dict]) -> List[Dict]:
        """Validate and clean generated code files."""
        processed = []
        for f in files:
            if "path" not in f or "content" not in f:
                continue
            
            # Clean up content
            content = f["content"]
            # Remove markdown code fences if present
            content = re.sub(r'^```\w*\n', '', content)
            content = re.sub(r'\n```$', '', content)
            
            processed.append({
                "path": f["path"],
                "content": content.strip(),
                "language": f.get("language", "python"),
            })
        
        return processed
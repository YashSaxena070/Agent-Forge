"""
Architect Agent with real LLM integration.
"""
import json
from typing import Any, Dict, List
from uuid import UUID

from apps.backend.src.agents.base import BaseAgent, AgentResult, agent_role
from apps.backend.src.agents.prompts import ARCHITECT_PROMPT
from apps.backend.src.core.llm import LLMProviderFactory, ArchitectureOutput
from apps.backend.src.models.entities import AgentRole
from apps.backend.src.core.telemetry import record_agent_metrics


@agent_role(AgentRole.ARCHITECT)
class ArchitectAgent(BaseAgent):
    """Architect Agent - Creates system architecture with real LLM."""
    
    role = AgentRole.ARCHITECT
    name = "Architect"
    description = "Designs system architecture, selects technologies, creates ADRs, defines APIs and data models"
    capabilities = [
        "system_design",
        "technology_selection",
        "api_design",
        "data_modeling",
        "architecture_decision_records",
        "scalability_planning",
    ]
    
    async def execute(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        db_session=None,
    ) -> AgentResult:
        """Execute the architect agent with real LLM."""
        user_stories = input_data.get("user_stories", [])
        requirements = input_data.get("requirements", {})
        constraints = input_data.get("constraints", {})
        existing_architecture = input_data.get("existing_architecture", {})
        tech_stack = input_data.get("tech_stack", [])
        
        messages = [
            {"role": "system", "content": "You are an expert software architect. Output valid JSON only."},
            {"role": "user", "content": ARCHITECT_PROMPT.format(
                user_stories=json.dumps(user_stories, indent=2),
                requirements=json.dumps(requirements, indent=2),
                constraints=json.dumps(constraints, indent=2),
                existing_architecture=json.dumps(existing_architecture, indent=2),
                tech_stack=json.dumps(tech_stack, indent=2),
            )},
        ]
        
        try:
            response = await LLMProviderFactory.complete(
                messages=messages,
                response_model=ArchitectureOutput,
                agent_role="architect",
                temperature=0.2,
                max_tokens=8000,
            )
            
            if not response.parsed:
                return AgentResult(
                    success=False,
                    error="Failed to parse architect output",
                    confidence=0.0,
                )
            
            arch_output = response.parsed.model_dump()
            
            # Extract implementation tasks
            impl_tasks = self._extract_implementation_tasks(arch_output)
            
            return AgentResult(
                success=True,
                output={
                    "result": arch_output,
                    "tokens_used": response.tokens_used,
                    "cost_usd": response.cost_usd,
                    "llm_provider": response.provider,
                    "llm_model": response.model,
                },
                artifacts=[
                    {
                        "name": "architecture_design.md",
                        "type": "document",
                        "content": self._format_architecture(arch_output),
                    },
                    {
                        "name": "api_spec.yaml",
                        "type": "spec",
                        "content": self._format_openapi_spec(arch_output.get("api_design", {})),
                    },
                ],
                next_actions=[
                    {"action": "create_tasks", "tasks": impl_tasks}
                ],
                confidence=0.9,
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Architect execution failed: {str(e)}",
                confidence=0.0,
            )
    
    def _extract_implementation_tasks(self, result: Dict) -> List[Dict]:
        """Extract implementation tasks from architecture output."""
        tasks = []
        
        # Component implementation tasks
        for component in result.get("architecture", {}).get("components", []):
            if component.get("type") == "service":
                tasks.append({
                    "title": f"Implement {component.get('name')}",
                    "description": f"Implement {component.get('type')} component using {component.get('technology')}",
                    "role": "backend",
                    "priority": "high",
                    "estimated_effort": "2d",
                    "tags": ["implementation", component.get("technology", "").lower()],
                })
            elif component.get("type") == "database":
                tasks.append({
                    "title": f"Set up {component.get('name')}",
                    "description": f"Configure {component.get('technology')} database with schemas",
                    "role": "database",
                    "priority": "high",
                    "estimated_effort": "1d",
                    "tags": ["database", component.get("technology", "").lower()],
                })
        
        return tasks
    
    def _format_architecture(self, result: Dict) -> str:
        """Format architecture as markdown."""
        lines = ["# Architecture Design\n"]
        arch = result.get("architecture", {})
        lines.append(f"**Style**: {arch.get('style', '')}")
        lines.append("\n## Components")
        for comp in arch.get("components", []):
            lines.append(f"- **{comp.get('name')}** ({comp.get('type')}): {comp.get('technology')}")
            lines.append(f"  - Responsibilities: {', '.join(comp.get('responsibilities', []))}")
        lines.append("\n## ADRs")
        for adr in result.get("adrs", []):
            lines.append(f"- **{adr.get('id')}**: {adr.get('title')} - {adr.get('status')}")
        return "\n".join(lines)
    
    def _format_openapi_spec(self, api_design: Dict) -> str:
        """Generate OpenAPI spec YAML."""
        lines = [
            "openapi: 3.0.0",
            "info:",
            "  title: AgentForge API",
            "  version: 1.0.0",
            "paths:",
        ]
        for endpoint in api_design.get("endpoints", []):
            path = endpoint.get("path", "")
            method = endpoint.get("method", "").lower()
            lines.append(f"  {path}:")
            lines.append(f"    {method}:")
            lines.append(f"      summary: {endpoint.get('description', '')}")
            lines.append(f"      responses:")
            lines.append(f"        '200':")
            lines.append(f"          description: Successful response")
        return "\n".join(lines)
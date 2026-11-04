"""
DevOps Agent with real LLM integration for deployment generation.
"""
import json
from typing import Any, Dict, List
from uuid import UUID

from apps.backend.src.agents.base import BaseAgent, AgentResult, agent_role
from apps.backend.src.agents.prompts import DEVOPS_PROMPT
from apps.backend.src.core.llm import LLMProviderFactory, DeploymentOutput, CodeFile
from apps.backend.src.models.entities import AgentRole
from apps.backend.src.core.telemetry import record_agent_metrics


@agent_role(AgentRole.DEVOPS)
class DevOpsAgent(BaseAgent):
    """DevOps Agent - Generates deployment infrastructure with real LLM."""
    
    role = AgentRole.DEVOPS
    name = "DevOps Engineer"
    description = "Creates Docker, Kubernetes, CI/CD, Helm charts, and deployment automation"
    capabilities = [
        "dockerfile_generation",
        "kubernetes_manifests",
        "ci_cd_pipelines",
        "helm_charts",
        "deployment_automation",
        "monitoring_setup",
        "infrastructure_as_code",
    ]
    
    async def execute(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        db_session=None,
    ) -> AgentResult:
        """Execute the DevOps agent with real LLM."""
        architecture = input_data.get("architecture", {})
        backend_code = input_data.get("backend_code", {})
        frontend_code = input_data.get("frontend_code", {})
        tech_stack = input_data.get("tech_stack", {})
        environment = input_data.get("environment", "staging")
        domain = input_data.get("domain", "agentforge.example.com")
        
        messages = [
            {"role": "system", "content": "You are an expert DevOps engineer. Output valid JSON only with complete, production-ready deployment configs."},
            {"role": "user", "content": DEVOPS_PROMPT.format(
                architecture=json.dumps(architecture, indent=2),
                backend_code=json.dumps(backend_code, indent=2),
                frontend_code=json.dumps(frontend_code, indent=2),
                tech_stack=json.dumps(tech_stack, indent=2),
                environment=environment,
                domain=domain,
            )},
        ]
        
        try:
            response = await LLMProviderFactory.complete(
                messages=messages,
                response_model=DeploymentOutput,
                agent_role="devops",
                temperature=0.1,
                max_tokens=16000,
            )
            
            if not response.parsed:
                return AgentResult(
                    success=False,
                    error="Failed to parse DevOps output",
                    confidence=0.0,
                )
            
            devops_output = response.parsed.model_dump()
            
            # Process all generated artifacts
            artifacts = []
            
            # Kubernetes manifests
            for manifest in devops_output.get("kubernetes_manifests", []):
                artifacts.append({
                    "name": manifest["path"].split("/")[-1],
                    "type": "config",
                    "content": manifest["content"],
                    "metadata": {"path": manifest["path"], "language": manifest.get("language", "yaml")},
                })
            
            # Dockerfile
            dockerfile = devops_output.get("dockerfile")
            if dockerfile:
                artifacts.append({
                    "name": dockerfile["path"],
                    "type": "config",
                    "content": dockerfile["content"],
                    "metadata": {"path": dockerfile["path"], "language": dockerfile.get("language", "dockerfile")},
                })
            
            # Docker Compose
            compose = devops_output.get("docker_compose")
            if compose:
                artifacts.append({
                    "name": compose["path"],
                    "type": "config",
                    "content": compose["content"],
                    "metadata": {"path": compose["path"], "language": compose.get("language", "yaml")},
                })
            
            # GitHub Actions
            github_actions = devops_output.get("github_actions")
            if github_actions:
                artifacts.append({
                    "name": github_actions["path"].split("/")[-1],
                    "type": "config",
                    "content": github_actions["content"],
                    "metadata": {"path": github_actions["path"], "language": github_actions.get("language", "yaml")},
                })
            
            # Helm charts
            for chart_file in devops_output.get("helm_chart", []):
                artifacts.append({
                    "name": chart_file["path"].split("/")[-1],
                    "type": "config",
                    "content": chart_file["content"],
                    "metadata": {"path": chart_file["path"], "language": chart_file.get("language", "yaml")},
                })
            
            # Scripts
            deploy_script = devops_output.get("deployment_script")
            if deploy_script:
                artifacts.append({
                    "name": deploy_script["path"].split("/")[-1],
                    "type": "code",
                    "content": deploy_script["content"],
                    "metadata": {"path": deploy_script["path"], "language": deploy_script.get("language", "bash")},
                })
            
            rollback_script = devops_output.get("rollback_script")
            if rollback_script:
                artifacts.append({
                    "name": rollback_script["path"].split("/")[-1],
                    "type": "code",
                    "content": rollback_script["content"],
                    "metadata": {"path": rollback_script["path"], "language": rollback_script.get("language", "bash")},
                })
            
            return AgentResult(
                success=True,
                output={
                    "result": devops_output,
                    "tokens_used": response.tokens_used,
                    "cost_usd": response.cost_usd,
                    "llm_provider": response.provider,
                    "llm_model": response.model,
                },
                artifacts=artifacts,
                next_actions=[
                    {"action": "deploy", "environment": environment}
                ],
                confidence=0.85,
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"DevOps execution failed: {str(e)}",
                confidence=0.0,
            )
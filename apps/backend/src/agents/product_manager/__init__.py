"""
Product Manager Agent - Handles requirements, user stories, and acceptance criteria.
"""
import json
from typing import Any, Dict, List
from uuid import UUID

from apps.backend.src.agents.base import BaseAgent, AgentResult, Tool, agent_role
from apps.backend.src.models.entities import AgentRole


@agent_role(AgentRole.PRODUCT_MANAGER)
class ProductManagerAgent(BaseAgent):
    """Product Manager Agent - Defines requirements and user stories."""
    
    role = AgentRole.PRODUCT_MANAGER
    name = "Product Manager"
    description = "Creates detailed requirements, user stories, acceptance criteria, and prioritizes features"
    capabilities = [
        "requirements_gathering",
        "user_story_creation",
        "acceptance_criteria",
        "feature_prioritization",
        "stakeholder_communication",
    ]
    
    tools = [
        Tool(
            name="create_user_stories",
            description="Create user stories from requirements",
            parameters={
                "type": "object",
                "properties": {
                    "features": {"type": "array", "items": {"type": "string"}},
                    "personas": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["features"],
            },
        ),
        Tool(
            name="define_acceptance_criteria",
            description="Define acceptance criteria for user stories",
            parameters={
                "type": "object",
                "properties": {
                    "user_stories": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["user_stories"],
            },
        ),
    ]
    
    prompt_template = """You are the Product Manager Agent for AgentForge.

Your role is to:
1. Transform high-level requirements into detailed user stories
2. Define clear acceptance criteria for each story
3. Prioritize features based on business value
4. Identify edge cases and error scenarios
5. Create product specifications

Input:
- Milestone: {milestone_name}
- Tasks: {tasks}
- Project Context: {project_context}
- Stakeholder Requirements: {stakeholder_requirements}

Output a structured JSON with:
{{
  "user_stories": [
    {{
      "id": "US-001",
      "title": "User story title",
      "description": "As a [persona], I want [action], so that [benefit]",
      "acceptance_criteria": [
        "Given [context], when [action], then [outcome]",
        "Given [context], when [action], then [outcome]"
      ],
      "priority": "high|medium|low",
      "story_points": 1|2|3|5|8|13,
      "dependencies": ["US-002"],
      "tags": ["frontend", "backend"]
    }}
  ],
  "product_spec": {{
    "overview": "Product overview",
    "key_features": ["feature1", "feature2"],
    "user_personas": ["persona1", "persona2"],
    "success_metrics": ["metric1", "metric2"],
    "out_of_scope": ["item1", "item2"]
  }},
  "questions_for_stakeholders": [
    "Question 1",
    "Question 2"
  ]
}}"""
    
    async def execute(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        db_session=None,
    ) -> AgentResult:
        """Execute the product manager agent."""
        milestone_name = input_data.get("milestone_name", "")
        tasks = input_data.get("tasks", [])
        project_context = input_data.get("project_context", {})
        stakeholder_requirements = input_data.get("stakeholder_requirements", "")
        
        prompt = self.prompt_template.format(
            milestone_name=milestone_name,
            tasks=json.dumps(tasks, indent=2),
            project_context=json.dumps(project_context, indent=2),
            stakeholder_requirements=stakeholder_requirements,
        )
        
        llm_response = await self._call_llm(
            prompt=prompt,
            system_prompt="You are an expert product manager. Output valid JSON only.",
            temperature=0.3,
            response_format="json",
        )
        
        try:
            result = json.loads(llm_response["content"])
            
            if not self._validate_output(result):
                return AgentResult(
                    success=False,
                    error="Invalid output structure",
                    confidence=0.0,
                )
            
            return AgentResult(
                success=True,
                output={
                    "result": result,
                    "tokens_used": llm_response.get("tokens_used", 0),
                    "cost_usd": llm_response.get("cost_usd", 0.0),
                    "llm_provider": llm_response.get("llm_provider"),
                    "llm_model": llm_response.get("llm_model"),
                },
                artifacts=[
                    {
                        "name": f"{milestone_name}_user_stories.md",
                        "type": "document",
                        "content": self._format_user_stories(result.get("user_stories", [])),
                    }
                ],
                next_actions=[
                    {"action": "create_tasks", "tasks": result.get("user_stories", [])}
                ],
                confidence=0.85,
            )
            
        except json.JSONDecodeError as e:
            return AgentResult(
                success=False,
                error=f"Failed to parse LLM response: {str(e)}",
                confidence=0.0,
            )
    
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate output structure."""
        return "user_stories" in output and isinstance(output["user_stories"], list)
    
    def _format_user_stories(self, stories: List[Dict]) -> str:
        """Format user stories as markdown."""
        lines = ["# User Stories\n"]
        for story in stories:
            lines.append(f"## {story.get('id', '')}: {story.get('title', '')}")
            lines.append(f"**Description**: {story.get('description', '')}")
            lines.append(f"**Priority**: {story.get('priority', '')}")
            lines.append(f"**Story Points**: {story.get('story_points', '')}")
            lines.append("**Acceptance Criteria**:")
            for ac in story.get("acceptance_criteria", []):
                lines.append(f"- {ac}")
            lines.append("")
        return "\n".join(lines)
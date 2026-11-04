"""
Production prompts for all agents.
"""
from apps.backend.src.agents.prompts.planner import PLANNER_PROMPT, PLANNER_EXAMPLES
from apps.backend.src.agents.prompts.architect import ARCHITECT_PROMPT, ARCHITECT_EXAMPLES
from apps.backend.src.agents.prompts.backend import BACKEND_PROMPT, BACKEND_EXAMPLES
from apps.backend.src.agents.prompts.devops import DEVOPS_PROMPT, DEVOPS_EXAMPLES

__all__ = [
    "PLANNER_PROMPT", "PLANNER_EXAMPLES",
    "ARCHITECT_PROMPT", "ARCHITECT_EXAMPLES",
    "BACKEND_PROMPT", "BACKEND_EXAMPLES",
    "DEVOPS_PROMPT", "DEVOPS_EXAMPLES",
]
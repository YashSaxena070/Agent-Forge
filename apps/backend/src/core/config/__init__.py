"""
Backend-specific configuration extending shared config.
"""
from services.shared.config import Settings, get_settings as get_shared_settings

# Re-export shared settings
settings = get_shared_settings()
get_settings = get_shared_settings

__all__ = ["settings", "get_settings", "Settings"]
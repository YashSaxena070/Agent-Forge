"""
Shared utility functions for AgentForge.
"""
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union
from urllib.parse import urlparse

T = TypeVar("T")


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate a short unique ID."""
    return uuid.uuid4().hex[:length]


def hash_content(content: str, algorithm: str = "sha256") -> str:
    """Generate hash of content."""
    hasher = hashlib.new(algorithm)
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


def hash_dict(data: Dict[str, Any], algorithm: str = "sha256") -> str:
    """Generate deterministic hash of dictionary."""
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hash_content(serialized, algorithm)


def slugify(text: str, max_length: int = 100) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text[:max_length]


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string (e.g., '2h', '1d', '30m') to seconds."""
    pattern = r"^(\d+)([smhd])$"
    match = re.match(pattern, duration_str.lower().strip())
    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)
    
    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }
    
    return value * multipliers.get(unit, 1)


def format_duration(seconds: int) -> str:
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize object to JSON."""
    return json.dumps(obj, default=str, **kwargs)


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely deserialize JSON."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """Execute function with exponential backoff retry."""
    import time
    import random
    
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                delay += random.uniform(0, 0.1 * delay)  # jitter
                time.sleep(delay)
    
    raise last_exception


async def async_retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """Execute async function with exponential backoff retry."""
    import asyncio
    import random
    
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                delay += random.uniform(0, 0.1 * delay)  # jitter
                await asyncio.sleep(delay)
    
    raise last_exception


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = filename.strip(". ")
    return filename[:255]


def parse_repository_url(url: str) -> Dict[str, Optional[str]]:
    """Parse repository URL to extract owner and repo."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")
    
    if len(parts) >= 2:
        return {
            "provider": parsed.netloc,
            "owner": parts[0],
            "repo": parts[1].replace(".git", ""),
            "branch": None,
        }
    return {"provider": parsed.netloc, "owner": None, "repo": None, "branch": None}


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """Mask secret for logging."""
    if len(secret) <= visible_chars * 2:
        return "*" * len(secret)
    return secret[:visible_chars] + "*" * (len(secret) - visible_chars * 2) + secret[-visible_chars:]


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: Optional[float] = None
    
    def __enter__(self) -> "Timer":
        self.start_time = now_utc()
        return self
    
    def __exit__(self, *args) -> None:
        self.end_time = now_utc()
        self.duration = (self.end_time - self.start_time).total_seconds()
    
    def __float__(self) -> float:
        if self.duration is None:
            if self.end_time and self.start_time:
                return (self.end_time - self.start_time).total_seconds()
            return 0.0
        return self.duration


def calculate_cost(tokens: int, model: str) -> float:
    """Estimate cost based on token usage and model."""
    # Approximate costs per 1K tokens (as of 2024)
    costs = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    }
    
    model_costs = costs.get(model, {"input": 0.01, "output": 0.03})
    # Assume 50/50 input/output split for estimation
    input_tokens = tokens // 2
    output_tokens = tokens - input_tokens
    
    return (input_tokens / 1000 * model_costs["input"]) + (output_tokens / 1000 * model_costs["output"])
"""
Unit tests for shared utilities.
"""
import pytest
from datetime import datetime, timezone
from uuid import UUID

from services.shared.utils import (
    generate_id,
    generate_short_id,
    hash_content,
    hash_dict,
    slugify,
    truncate,
    parse_duration,
    format_duration,
    now_utc,
    safe_json_dumps,
    safe_json_loads,
    deep_merge,
    flatten_dict,
    chunk_list,
    sanitize_filename,
    parse_repository_url,
    mask_secret,
    Timer,
    calculate_cost,
)


class TestIdGeneration:
    """Tests for ID generation utilities."""

    def test_generate_id(self):
        """Test generating a UUID."""
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        # Should be valid UUID
        UUID(id1)

    def test_generate_short_id(self):
        """Test generating a short ID."""
        short_id = generate_short_id(8)
        assert len(short_id) == 8
        # Should be hex characters
        assert all(c in '0123456789abcdef' for c in short_id)


class TestHashing:
    """Tests for hashing utilities."""

    def test_hash_content(self):
        """Test hashing string content."""
        hash1 = hash_content("test content")
        hash2 = hash_content("test content")
        hash3 = hash_content("different content")
        assert hash1 == hash2  # Deterministic
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA256 hex length

    def test_hash_dict(self):
        """Test hashing dictionary."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 2, "a": 1}  # Different order
        dict3 = {"a": 1, "b": 3}
        assert hash_dict(dict1) == hash_dict(dict2)  # Order independent
        assert hash_dict(dict1) != hash_dict(dict3)


class TestStringUtilities:
    """Tests for string utilities."""

    def test_slugify(self):
        """Test slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test_Case") == "test-case"
        assert slugify("Special!@#Chars") == "specialchars"
        assert slugify("  leading trailing  ") == "leading-trailing"
        assert slugify("Multiple   Spaces") == "multiple-spaces"

    def test_truncate(self):
        """Test string truncation."""
        long_text = "a" * 100
        truncated = truncate(long_text, 50)
        assert len(truncated) == 50
        assert truncated.endswith("...")
        
        short_text = "short"
        assert truncate(short_text, 50) == short_text

    def test_parse_duration(self):
        """Test parsing duration strings."""
        assert parse_duration("30s") == 30
        assert parse_duration("5m") == 300
        assert parse_duration("2h") == 7200
        assert parse_duration("1d") == 86400
        assert parse_duration("invalid") is None

    def test_format_duration(self):
        """Test formatting durations."""
        assert format_duration(30) == "30s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(3661) == "1h 1m"
        assert format_duration(90061) == "1d 1h"

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename('file<name>.txt') == 'file_name_.txt'
        assert sanitize_filename('normal_file.py') == 'normal_file.py'
        assert sanitize_filename('path/to/file') == 'path_to_file'

    def test_parse_repository_url(self):
        """Test parsing repository URLs."""
        result = parse_repository_url("https://github.com/owner/repo.git")
        assert result["provider"] == "github.com"
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"
        
        result = parse_repository_url("https://gitlab.com/group/project")
        assert result["provider"] == "gitlab.com"

    def test_mask_secret(self):
        """Test secret masking."""
        assert mask_secret("abcdefgh") == "abcd****efgh"
        assert mask_secret("short") == "*****"
        assert mask_secret("a") == "*"


class TestDateTimeUtilities:
    """Tests for datetime utilities."""

    def test_now_utc(self):
        """Test getting current UTC time."""
        now = now_utc()
        assert now.tzinfo == timezone.utc
        # Should be close to actual time
        assert abs((datetime.now(timezone.utc) - now).total_seconds()) < 1


class TestJSONUtilities:
    """Tests for JSON utilities."""

    def test_safe_json_dumps(self):
        """Test safe JSON serialization."""
        data = {"date": datetime(2024, 1, 1), "set": {1, 2, 3}}
        json_str = safe_json_dumps(data)
        assert "2024-01-01" in json_str
        assert "1" in json_str  # Sets become lists

    def test_safe_json_loads(self):
        """Test safe JSON deserialization."""
        assert safe_json_loads('{"a": 1}') == {"a": 1}
        assert safe_json_loads('invalid') is None
        assert safe_json_loads('invalid', default={}) == {}


class TestDictUtilities:
    """Tests for dictionary utilities."""

    def test_deep_merge(self):
        """Test deep dictionary merging."""
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}, "e": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested = {"a": {"b": {"c": 1}}, "d": 2}
        flat = flatten_dict(nested)
        assert flat == {"a.b.c": 1, "d": 2}


class TestListUtilities:
    """Tests for list utilities."""

    def test_chunk_list(self):
        """Test list chunking."""
        items = list(range(10))
        chunks = chunk_list(items, 3)
        assert chunks == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


class TestTimer:
    """Tests for Timer context manager."""

    def test_timer_context(self):
        """Test timer as context manager."""
        with Timer() as timer:
            # Small delay
            import time
            time.sleep(0.01)
        
        assert timer.duration is not None
        assert timer.duration > 0.01

    def test_timer_float(self):
        """Test timer float conversion."""
        timer = Timer()
        timer.start_time = datetime.now(timezone.utc)
        timer.end_time = datetime.now(timezone.utc)
        assert float(timer) >= 0


class TestCostCalculation:
    """Tests for cost calculation."""

    def test_calculate_cost_gpt4(self):
        """Test cost calculation for GPT-4."""
        cost = calculate_cost(1000, "gpt-4-turbo-preview")
        # 500 input * 0.01/1000 + 500 output * 0.03/1000 = 0.005 + 0.015 = 0.02
        assert abs(cost - 0.02) < 0.001

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model."""
        cost = calculate_cost(1000, "unknown-model")
        # Uses default costs
        assert cost > 0
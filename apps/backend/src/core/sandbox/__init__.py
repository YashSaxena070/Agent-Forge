"""
Code sandbox for testing generated code in isolated environment.
"""
import asyncio
import tempfile
import os
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class SandboxResult:
    """Result of code execution in sandbox."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    artifacts: List[str] = None


class CodeSandbox:
    """Isolated code execution environment."""
    
    def __init__(
        self,
        base_image: str = "python:3.11-slim",
        timeout: int = 60,
        memory_limit: str = "512m",
        cpu_limit: float = 1.0,
    ):
        self.base_image = base_image
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self._docker_client = None
    
    async def _get_docker_client(self):
        """Get Docker client."""
        if self._docker_client is None:
            import docker
            self._docker_client = docker.DockerClient.from_env()
        return self._docker_client
    
    async def execute_python(
        self,
        code: str,
        requirements: List[str] = None,
        files: Dict[str, str] = None,
        env_vars: Dict[str, str] = None,
    ) -> SandboxResult:
        """Execute Python code in isolated container."""
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            
            # Write main code
            (workdir / "main.py").write_text(code)
            
            # Write additional files
            if files:
                for path, content in files.items():
                    file_path = workdir / path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)
            
            # Write requirements
            if requirements:
                (workdir / "requirements.txt").write_text("\n".join(requirements))
            
            # Build Dockerfile
            dockerfile = self._generate_dockerfile(requirements)
            (workdir / "Dockerfile").write_text(dockerfile)
            
            # Build and run
            return await self._run_container(workdir, env_vars)
    
    def _generate_dockerfile(self, requirements: List[str] = None) -> str:
        """Generate Dockerfile for sandbox."""
        lines = [
            "FROM python:3.11-slim",
            "WORKDIR /app",
            "RUN pip install --no-cache-dir pytest pytest-asyncio httpx",
        ]
        
        if requirements:
            reqs = " ".join(requirements)
            lines.append(f"RUN pip install --no-cache-dir {reqs}")
        
        lines.extend([
            "COPY . .",
            "CMD [\"python\", \"main.py\"]",
        ])
        
        return "\n".join(lines)
    
    async def _run_container(
        self,
        workdir: Path,
        env_vars: Dict[str, str] = None,
    ) -> SandboxResult:
        """Build and run container."""
        import docker
        import time
        
        client = await self._get_docker_client()
        
        try:
            # Build image
            image, build_logs = client.images.build(
                path=str(workdir),
                tag=f"sandbox-{os.urandom(8).hex()}",
                rm=True,
                forcerm=True,
            )
            
            # Run container
            start_time = time.time()
            container = client.containers.run(
                image.id,
                detach=True,
                mem_limit=self.memory_limit,
                cpu_quota=int(self.cpu_limit * 100000),
                environment=env_vars or {},
                network_mode="none",  # No network access
            )
            
            try:
                # Wait for completion with timeout
                exit_code = container.wait(timeout=self.timeout)
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Get logs
                logs = container.logs(stdout=True, stderr=True).decode("utf-8")
                
                # Separate stdout/stderr (simplified)
                stdout = logs
                stderr = ""
                
                return SandboxResult(
                    success=exit_code == 0,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                )
            finally:
                container.remove(force=True)
                
        except docker.errors.ContainerError as e:
            return SandboxResult(
                success=False,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else str(e),
                exit_code=e.exit_status,
                duration_ms=0,
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration_ms=0,
            )
        finally:
            # Clean up image
            try:
                client.images.remove(image.id, force=True)
            except Exception:
                pass


class TestRunner:
    """Run tests for generated code."""
    
    def __init__(self, sandbox: CodeSandbox = None):
        self.sandbox = sandbox or CodeSandbox()
    
    async def run_tests(
        self,
        source_files: Dict[str, str],
        test_files: Dict[str, str],
        requirements: List[str] = None,
    ) -> Dict[str, Any]:
        """Run tests in sandbox."""
        
        all_files = {**source_files, **test_files}
        
        # Find test entry point
        test_code = self._generate_test_runner(test_files)
        
        result = await self.sandbox.execute_python(
            code=test_code,
            requirements=requirements,
            files=all_files,
        )
        
        return {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "passed": result.success and "passed" in result.stdout.lower(),
        }
    
    def _generate_test_runner(self, test_files: Dict[str, str]) -> str:
        """Generate test runner code."""
        return """
import pytest
import sys

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", "--tb=short"] + sys.argv[1:]))
"""
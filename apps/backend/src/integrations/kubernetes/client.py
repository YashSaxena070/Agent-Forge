"""
Kubernetes integration for cluster operations.
"""
from typing import Any, Dict, List, Optional
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import MCPError
from apps.backend.src.integrations.mcp.base import MCPClient, MCPTool, MCPResource


class KubernetesClient:
    """Kubernetes API client."""
    
    def __init__(self):
        # Load kubeconfig
        if settings.KUBECONFIG:
            config.load_kube_config(config_file=settings.KUBECONFIG)
        else:
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.custom_objects = client.CustomObjectsApi()
    
    def apply_manifest(self, manifest: Dict[str, Any], namespace: str = "default") -> Any:
        """Apply Kubernetes manifest."""
        kind = manifest.get("kind")
        name = manifest.get("metadata", {}).get("name")
        namespace = manifest.get("metadata", {}).get("namespace", namespace)
        
        if kind == "Deployment":
            return self._apply_deployment(manifest, namespace)
        elif kind == "Service":
            return self._apply_service(manifest, namespace)
        elif kind == "Ingress":
            return self._apply_ingress(manifest, namespace)
        elif kind == "ConfigMap":
            return self._apply_configmap(manifest, namespace)
        elif kind == "Secret":
            return self._apply_secret(manifest, namespace)
        elif kind == "PersistentVolumeClaim":
            return self._apply_pvc(manifest, namespace)
        
        raise ValueError(f"Unsupported kind: {kind}")
    
    def _apply_deployment(self, manifest: Dict, namespace: str) -> Any:
        """Apply Deployment manifest."""
        try:
            existing = self.apps_v1.read_namespaced_deployment(
                name=manifest["metadata"]["name"],
                namespace=namespace,
            )
            return self.apps_v1.replace_namespaced_deployment(
                name=manifest["metadata"]["name"],
                namespace=namespace,
                body=manifest,
            )
        except ApiException as e:
            if e.status == 404:
                return self.apps_v1.create_namespaced_deployment(
                    namespace=namespace,
                    body=manifest,
                )
            raise
    
    def _apply_service(self, manifest: Dict, namespace: str) -> Any:
        """Apply Service manifest."""
        try:
            existing = self.core_v1.read_namespaced_service(
                name=manifest["metadata"]["name"],
                namespace=namespace,
            )
            return self.core_v1.replace_namespaced_service(
                name=manifest["metadata"]["name"],
                namespace=namespace,
                body=manifest,
            )
        except ApiException as e:
            if e.status == 404:
                return self.core_v1.create_namespaced_service(
                    namespace=namespace,
                    body=manifest,
                )
            raise
    
    def _apply_ingress(self, manifest: Dict, namespace: str) -> Any:
        """Apply Ingress manifest."""
        try:
            existing = self.networking_v1.read_namespaced_ingress(
                name=manifest["metadata"]["name"],
                namespace=namespace,
            )
            return self.networking_v1.replace_namespaced_ingress(
                name=manifest["metadata"]["name"],
                namespace=namespace,
                body=manifest,
            )
        except ApiException as e:
            if e.status == 404:
                return self.networking_v1.create_namespaced_ingress(
                    namespace=namespace,
                    body=manifest,
                )
            raise
    
    def _apply_configmap(self, manifest: Dict, namespace: str) -> Any:
        """Apply ConfigMap manifest."""
        try:
            existing = self.core_v1.read_namespaced_config_map(
                name=manifest["metadata"]["name"],
                namespace=namespace,
            )
            return self.core_v1.replace_namespaced_config_map(
                name=manifest["metadata"]["name"],
                namespace=namespace,
                body=manifest,
            )
        except ApiException as e:
            if e.status == 404:
                return self.core_v1.create_namespaced_config_map(
                    namespace=namespace,
                    body=manifest,
                )
            raise
    
    def _apply_secret(self, manifest: Dict, namespace: str) -> Any:
        """Apply Secret manifest."""
        try:
            existing = self.core_v1.read_namespaced_secret(
                name=manifest["metadata"]["name"],
                namespace=namespace,
            )
            return self.core_v1.replace_namespaced_secret(
                name=manifest["metadata"]["name"],
                namespace=namespace,
                body=manifest,
            )
        except ApiException as e:
            if e.status == 404:
                return self.core_v1.create_namespaced_secret(
                    namespace=namespace,
                    body=manifest,
                )
            raise
    
    def _apply_pvc(self, manifest: Dict, namespace: str) -> Any:
        """Apply PVC manifest."""
        try:
            existing = self.core_v1.read_namespaced_persistent_volume_claim(
                name=manifest["metadata"]["name"],
                namespace=namespace,
            )
            return self.core_v1.replace_namespaced_persistent_volume_claim(
                name=manifest["metadata"]["name"],
                namespace=namespace,
                body=manifest,
            )
        except ApiException as e:
            if e.status == 404:
                return self.core_v1.create_namespaced_persistent_volume_claim(
                    namespace=namespace,
                    body=manifest,
                )
            raise
    
    def wait_for_rollout(self, deployment_name: str, namespace: str = "default", timeout: int = 300) -> bool:
        """Wait for deployment rollout to complete."""
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            deployment = self.apps_v1.read_namespaced_deployment(deployment_name, namespace)
            
            if (deployment.status.ready_replicas == deployment.spec.replicas and
                deployment.status.updated_replicas == deployment.spec.replicas and
                deployment.status.available_replicas == deployment.spec.replicas):
                return True
            
            time.sleep(5)
        
        return False
    
    def rollback_deployment(self, deployment_name: str, namespace: str = "default", revision: int = None) -> Any:
        """Rollback deployment to previous revision."""
        if revision:
            # Rollback to specific revision
            return self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body={
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "deployment.kubernetes.io/revision": str(revision)
                                }
                            }
                        }
                    }
                },
            )
        else:
            # Rollback to previous revision
            return self.apps_v1.rollback_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
            )
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default", tail: int = 100) -> str:
        """Get pod logs."""
        return self.core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail,
        )
    
    def scale_deployment(self, deployment_name: str, replicas: int, namespace: str = "default") -> Any:
        """Scale deployment."""
        return self.apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body={"spec": {"replicas": replicas}},
        )
    
    def list_pods(self, namespace: str = "default", label_selector: str = None) -> List[Any]:
        """List pods."""
        return self.core_v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
        ).items
    
    def get_deployment_status(self, deployment_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Get deployment status."""
        deployment = self.apps_v1.read_namespaced_deployment(deployment_name, namespace)
        
        return {
            "name": deployment.metadata.name,
            "replicas": deployment.spec.replicas,
            "ready_replicas": deployment.status.ready_replicas or 0,
            "updated_replicas": deployment.status.updated_replicas or 0,
            "available_replicas": deployment.status.available_replicas or 0,
            "conditions": [
                {"type": c.type, "status": c.status, "reason": c.reason, "message": c.message}
                for c in (deployment.status.conditions or [])
            ],
        }


class KubernetesMCPClient(MCPClient):
    """MCP client for Kubernetes operations."""
    
    def __init__(self):
        super().__init__("kubernetes://cluster")
        self.k8s_client = KubernetesClient()
    
    async def initialize(self) -> bool:
        """Initialize Kubernetes connection."""
        try:
            self.k8s_client.core_v1.list_namespace(limit=1)
            return True
        except Exception:
            return False
    
    async def list_tools(self) -> List[MCPTool]:
        """List available Kubernetes tools."""
        self._tools = [
            MCPTool(
                name="apply_manifest",
                description="Apply Kubernetes manifest",
                input_schema={
                    "type": "object",
                    "properties": {
                        "manifest": {"type": "object"},
                        "namespace": {"type": "string"},
                    },
                    "required": ["manifest"],
                },
            ),
            MCPTool(
                name="wait_for_rollout",
                description="Wait for deployment rollout",
                input_schema={
                    "type": "object",
                    "properties": {
                        "deployment_name": {"type": "string"},
                        "namespace": {"type": "string"},
                        "timeout": {"type": "integer"},
                    },
                    "required": ["deployment_name"],
                },
            ),
            MCPTool(
                name="rollback_deployment",
                description="Rollback deployment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "deployment_name": {"type": "string"},
                        "namespace": {"type": "string"},
                        "revision": {"type": "integer"},
                    },
                    "required": ["deployment_name"],
                },
            ),
            MCPTool(
                name="get_pod_logs",
                description="Get pod logs",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pod_name": {"type": "string"},
                        "namespace": {"type": "string"},
                        "tail": {"type": "integer"},
                    },
                    "required": ["pod_name"],
                },
            ),
            MCPTool(
                name="scale_deployment",
                description="Scale deployment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "deployment_name": {"type": "string"},
                        "replicas": {"type": "integer"},
                        "namespace": {"type": "string"},
                    },
                    "required": ["deployment_name", "replicas"],
                },
            ),
            MCPTool(
                name="get_deployment_status",
                description="Get deployment status",
                input_schema={
                    "type": "object",
                    "properties": {
                        "deployment_name": {"type": "string"},
                        "namespace": {"type": "string"},
                    },
                    "required": ["deployment_name"],
                },
            ),
        ]
        return self._tools
    
    async def list_resources(self) -> List[MCPResource]:
        """List available Kubernetes resources."""
        self._resources = [
            MCPResource(
                uri="k8s://namespaces",
                name="Namespaces",
                description="List of Kubernetes namespaces",
            ),
            MCPResource(
                uri="k8s://nodes",
                name="Nodes",
                description="List of Kubernetes nodes",
            ),
        ]
        return self._resources
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a Kubernetes tool."""
        namespace = arguments.get("namespace", "default")
        
        if name == "apply_manifest":
            result = self.k8s_client.apply_manifest(arguments["manifest"], namespace)
            return {"kind": result.kind, "name": result.metadata.name}
        
        elif name == "wait_for_rollout":
            success = self.k8s_client.wait_for_rollout(
                deployment_name=arguments["deployment_name"],
                namespace=namespace,
                timeout=arguments.get("timeout", 300),
            )
            return {"success": success}
        
        elif name == "rollback_deployment":
            result = self.k8s_client.rollback_deployment(
                deployment_name=arguments["deployment_name"],
                namespace=namespace,
                revision=arguments.get("revision"),
            )
            return {"name": result.metadata.name}
        
        elif name == "get_pod_logs":
            logs = self.k8s_client.get_pod_logs(
                pod_name=arguments["pod_name"],
                namespace=namespace,
                tail=arguments.get("tail", 100),
            )
            return {"logs": logs}
        
        elif name == "scale_deployment":
            result = self.k8s_client.scale_deployment(
                deployment_name=arguments["deployment_name"],
                replicas=arguments["replicas"],
                namespace=namespace,
            )
            return {"name": result.metadata.name, "replicas": result.spec.replicas}
        
        elif name == "get_deployment_status":
            status = self.k8s_client.get_deployment_status(
                deployment_name=arguments["deployment_name"],
                namespace=namespace,
            )
            return status
        
        raise MCPError("kubernetes", f"Unknown tool: {name}")
    
    async def read_resource(self, uri: str) -> Any:
        """Read a Kubernetes resource."""
        if uri == "k8s://namespaces":
            namespaces = self.k8s_client.core_v1.list_namespace()
            return [{"name": n.metadata.name, "status": n.status.phase} for n in namespaces.items]
        
        elif uri == "k8s://nodes":
            nodes = self.k8s_client.core_v1.list_node()
            return [
                {
                    "name": n.metadata.name,
                    "status": [c.status for c in n.status.conditions if c.type == "Ready"][0],
                    "roles": n.metadata.labels.get("node-role.kubernetes.io/control-plane", "worker"),
                }
                for n in nodes.items
            ]
        
        raise MCPError("kubernetes", f"Unknown resource: {uri}")
    
    async def close(self):
        """Close Kubernetes client."""
        pass


# Global instance
_k8s_client: Optional[KubernetesClient] = None
_k8s_mcp_client: Optional[KubernetesMCPClient] = None


def get_kubernetes_client() -> KubernetesClient:
    """Get or create Kubernetes client."""
    global _k8s_client
    if _k8s_client is None:
        _k8s_client = KubernetesClient()
    return _k8s_client


def get_kubernetes_mcp_client() -> KubernetesMCPClient:
    """Get or create Kubernetes MCP client."""
    global _k8s_mcp_client
    if _k8s_mcp_client is None:
        _k8s_mcp_client = KubernetesMCPClient()
    return _k8s_mcp_client
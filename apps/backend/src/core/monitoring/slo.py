"""
SLO/SLI Monitoring with Alerting
"""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from apps.backend.src.core.config import settings
from apps.backend.src.core.database import db_manager
from apps.backend.src.core.telemetry import get_meter
from apps.backend.src.core.audit import audit_log, AuditEventType, AuditSeverity
from apps.backend.src.core.tools import get_tool_executor


class SLIType(str, Enum):
    """Types of Service Level Indicators."""
    AVAILABILITY = "availability"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    DURABILITY = "durability"
    CORRECTNESS = "correctness"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


@dataclass
class SLIDefinition:
    """Definition of a Service Level Indicator."""
    name: str
    type: SLIType
    description: str
    query: str  # PromQL query
    good_query: str  # Query for "good" events
    total_query: str  # Query for "total" events
    unit: str = ""
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class SLOTarget:
    """SLO target definition."""
    sli_name: str
    target: float  # 0.999 for 99.9%
    window: str = "30d"  # Rolling window
    description: str = ""


class SLIResult(BaseModel):
    """Result of SLI evaluation."""
    sli_name: str
    value: float
    target: float
    met: bool
    error_budget_remaining: float
    error_budget_burn_rate: float
    window: str
    timestamp: datetime


class AlertRule(BaseModel):
    """Alert rule definition."""
    rule_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    severity: AlertSeverity
    condition: str  # PromQL condition
    for_duration: str = "5m"
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    runbook_url: Optional[str] = None
    enabled: bool = True


class Alert(BaseModel):
    """Active alert."""
    alert_id: UUID = Field(default_factory=uuid4)
    rule_id: UUID
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.FIRING
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    value: float
    starts_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ends_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None


class NotificationChannel(BaseModel):
    """Notification channel for alerts."""
    channel_id: UUID = Field(default_factory=uuid4)
    name: str
    type: str  # slack, email, pagerduty, webhook, sms
    config: Dict[str, Any]
    severity_filter: List[str] = Field(default_factory=lambda: ["warning", "critical"])
    enabled: bool = True


class SLODashboard(BaseModel):
    """SLO dashboard data."""
    service_name: str
    slos: List[SLIResult]
    overall_health: float  # 0-1
    error_budget_total: float
    error_budget_consumed: float
    alerts_active: int
    alerts_critical: int
    last_updated: datetime


class SLOMonitor:
    """Service Level Objective monitoring."""
    
    def __init__(self):
        self.slis: Dict[str, SLIDefinition] = {}
        self.slo_targets: Dict[str, SLOTarget] = {}
        self.alert_rules: Dict[UUID, AlertRule] = {}
        self.active_alerts: Dict[UUID, Alert] = {}
        self.notification_channels: List[NotificationChannel] = []
        self._prometheus_url = settings.PROMETHEUS_URL or "http://prometheus:9090"
        self._client = None
    
    def register_sli(self, sli: SLIDefinition):
        """Register an SLI."""
        self.slis[sli.name] = sli
    
    def register_slo(self, target: SLOTarget):
        """Register an SLO target."""
        self.slo_targets[target.sli_name] = target
    
    def register_alert_rule(self, rule: AlertRule):
        """Register an alert rule."""
        self.alert_rules[rule.rule_id] = rule
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel."""
        self.notification_channels.append(channel)
    
    async def evaluate_sli(self, sli_name: str, window: str = "30d") -> SLIResult:
        """Evaluate a single SLI."""
        sli = self.slis.get(sli_name)
        target = self.slo_targets.get(sli_name)
        
        if not sli or not target:
            raise ValueError(f"SLI or target not found: {sli_name}")
        
        # Query Prometheus for good and total events
        good_count = await self._query_prometheus(sli.good_query.replace("$window", window))
        total_count = await self._query_prometheus(sli.total_query.replace("$window", window))
        
        if total_count == 0:
            value = 1.0
        else:
            value = good_count / total_count
        
        met = value >= target.target
        error_budget = 1.0 - target.target
        error_budget_remaining = max(0, value - (1.0 - error_budget)) / error_budget if error_budget > 0 else 1.0
        
        # Calculate burn rate (how fast we're consuming error budget)
        # Compare 1h window vs 30d window
        recent_good = await self._query_prometheus(sli.good_query.replace("$window", "1h"))
        recent_total = await self._query_prometheus(sli.total_query.replace("$window", "1h"))
        recent_value = recent_good / recent_total if recent_total > 0 else 1.0
        expected_budget_consumption = (1.0 - target.target) / (30 * 24)  # per hour
        actual_budget_consumption = 1.0 - recent_value
        burn_rate = actual_budget_consumption / expected_budget_consumption if expected_budget_consumption > 0 else 1.0
        
        return SLIResult(
            sli_name=sli_name,
            value=value,
            target=target.target,
            met=met,
            error_budget_remaining=error_budget_remaining,
            error_budget_burn_rate=burn_rate,
            window=window,
            timestamp=datetime.now(timezone.utc),
        )
    
    async def evaluate_all_slos(self, window: str = "30d") -> List[SLIResult]:
        """Evaluate all registered SLOs."""
        results = []
        for sli_name in self.slo_targets:
            try:
                result = await self.evaluate_sli(sli_name, window)
                results.append(result)
            except Exception as e:
                # Log error but continue
                print(f"Error evaluating SLI {sli_name}: {e}")
        return results
    
    async def check_alerts(self) -> List[Alert]:
        """Evaluate all alert rules and return firing alerts."""
        new_alerts = []
        
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Query Prometheus for alert condition
                value = await self._query_prometheus(rule.condition)
                
                # Simple threshold check (in practice, use Prometheus Alertmanager)
                is_firing = value > 0  # Simplified
                
                existing_alert = next(
                    (a for a in self.active_alerts.values() if a.rule_id == rule.rule_id),
                    None,
                )
                
                if is_firing and not existing_alert:
                    # New alert
                    alert = Alert(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        status=AlertStatus.FIRING,
                        labels=rule.labels,
                        annotations=rule.annotations,
                        value=value,
                    )
                    self.active_alerts[alert.alert_id] = alert
                    await self._send_notifications(alert)
                    
                elif not is_firing and existing_alert:
                    # Resolve alert
                    existing_alert.status = AlertStatus.RESOLVED
                    existing_alert.ends_at = datetime.now(timezone.utc)
                    
            except Exception as e:
                print(f"Error checking alert rule {rule.name}: {e}")
        
        return list(self.active_alerts.values())
    
    async def acknowledge_alert(self, alert_id: UUID, user_id: UUID) -> bool:
        """Acknowledge an alert."""
        alert = self.active_alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.acknowledged_by = user_id
            return True
        return False
    
    async def resolve_alert(self, alert_id: UUID) -> bool:
        """Resolve an alert."""
        alert = self.active_alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc)
            return True
        return False
    
    async def silence_alert(self, alert_id: UUID, duration: timedelta) -> bool:
        """Silence an alert for a duration."""
        alert = self.active_alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.SILENCED
            alert.ends_at = datetime.now(timezone.utc) + duration
            return True
        return False
    
    async def get_dashboard(self, service_name: str = "agentforge") -> SLODashboard:
        """Get SLO dashboard data."""
        slos = await self.evaluate_all_slos()
        
        overall_health = sum(1 for s in slos if s.met) / len(slos) if slos else 1.0
        error_budget_total = sum(1.0 - self.slo_targets.get(s.sli_name, SLOTarget(sli_name="", target=0.999)).target for s in slos)
        error_budget_consumed = sum((1.0 - s.value) for s in slos)
        
        alerts = list(self.active_alerts.values())
        active_alerts = [a for a in alerts if a.status == AlertStatus.FIRING]
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        return SLODashboard(
            service_name=service_name,
            slos=await self.evaluate_all_slos(),
            overall_health=sum(1 for s in slos if s.met) / len(slos) if slos else 1.0,
            error_budget_total=sum(1.0 - self.slo_targets.get(s.sli_name, SLOTarget(sli_name="", target=0.999)).target for s in slos),
            error_budget_consumed=sum(max(0, 1.0 - s.value) for s in slos),
            alerts_active=len(active_alerts),
            alerts_critical=len(critical_alerts),
            last_updated=datetime.now(timezone.utc),
        )
    
    async def _query_prometheus(self, query: str) -> float:
        """Query Prometheus and return scalar value."""
        # In production, use prometheus-client or httpx to query Prometheus
        # This is a placeholder
        return 1.0


class SLOReporter:
    """Generate SLO reports."""
    
    def __init__(self, monitor: SLOMonitor):
        self.monitor = monitor
    
    async def generate_report(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Generate SLO compliance report."""
        slos = await self.monitor.evaluate_all_slos("30d")
        
        met_count = sum(1 for s in slos if s.met)
        total = len(slos)
        
        report = {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "summary": {
                "total_slos": len(slos),
                "met": sum(1 for s in slos if s.met),
                "missed": len(slos) - sum(1 for s in slos if s.met),
                "compliance_rate": sum(1 for s in slos if s.met) / len(slos) if slos else 1.0,
            },
            "slos": [
                {
                    "name": s.sli_name,
                    "value": s.value,
                    "target": s.target,
                    "met": s.met,
                    "error_budget_remaining": s.error_budget_remaining,
                    "burn_rate": s.error_budget_burn_rate,
                }
                for s in slos
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        return report


# Default SLI definitions for AgentForge
DEFAULT_SLIS = {
    "api_availability": SLIDefinition(
        name="api_availability",
        type=SLIType.AVAILABILITY,
        description="API request success rate",
        query='sum(rate(http_requests_total{job="agentforge-backend"}[5m]))',
        good_query='sum(rate(http_requests_total{job="agentforge-backend",status=~"2.."}[5m]))',
        total_query='sum(rate(http_requests_total{job="agentforge-backend"}[5m]))',
        unit="ratio",
    ),
    "api_latency_p99": SLIDefinition(
        name="api_latency_p99",
        type=SLIType.LATENCY,
        description="API p99 latency under 500ms",
        query='histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="agentforge-backend"}[5m])) by (le))',
        good_query='histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="agentforge-backend",le="0.5"}[5m])) by (le))',
        total_query='histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="agentforge-backend"}[5m])) by (le))',
        unit="seconds",
    ),
    "workflow_success_rate": SLIDefinition(
        name="workflow_success_rate",
        type=SLIType.CORRECTNESS,
        description="Workflow completion success rate",
        query='sum(rate(workflow_completed_total[5m]))',
        good_query='sum(rate(workflow_completed_total{status="success"}[5m]))',
        total_query='sum(rate(workflow_completed_total[5m]))',
        unit="ratio",
    ),
    "deployment_success_rate": SLIDefinition(
        name="deployment_success_rate",
        type=SLIType.CORRECTNESS,
        description="Deployment success rate",
        query='sum(rate(deployment_completed_total[5m]))',
        good_query='sum(rate(deployment_completed_total{status="success"}[5m]))',
        total_query='sum(rate(deployment_completed_total[5m]))',
        unit="ratio",
    ),
    "agent_execution_success": SLIDefinition(
        name="agent_execution_success",
        type=SLIType.CORRECTNESS,
        description="Agent execution success rate",
        query='sum(rate(agent_execution_completed_total[5m]))',
        good_query='sum(rate(agent_execution_completed_total{status="success"}[5m]))',
        total_query='sum(rate(agent_execution_completed_total[5m]))',
        unit="ratio",
    ),
}

DEFAULT_SLO_TARGETS = {
    "api_availability": SLOTarget(
        sli_name="api_availability",
        target=0.999,  # 99.9%
        window="30d",
        description="API should be available 99.9% of the time",
    ),
    "api_latency_p99": SLOTarget(
        sli_name="api_latency_p99",
        target=0.95,  # 95% of requests under 500ms
        window="30d",
        description="95% of API requests should complete within 500ms",
    ),
    "workflow_success_rate": SLOTarget(
        sli_name="workflow_success_rate",
        target=0.99,  # 99%
        window="30d",
        description="99% of workflows should complete successfully",
    ),
    "deployment_success_rate": SLOTarget(
        sli_name="deployment_success_rate",
        target=0.995,  # 99.5%
        window="30d",
        description="99.5% of deployments should succeed",
    ),
    "agent_execution_success": SLOTarget(
        sli_name="agent_execution_success",
        target=0.95,  # 95%
        window="30d",
        description="95% of agent executions should succeed",
    ),
}

DEFAULT_ALERT_RULES = [
    AlertRule(
        name="HighErrorRate",
        description="API error rate exceeds 1%",
        severity=AlertSeverity.CRITICAL,
        condition='sum(rate(http_requests_total{job="agentforge-backend",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="agentforge-backend"}[5m])) > 0.01',
        for_duration="5m",
        labels={"team": "platform", "service": "api"},
        annotations={"summary": "High API error rate", "runbook": "https://runbooks.agentforge.com/high-error-rate"},
    ),
    AlertRule(
        name="HighLatency",
        description="API p99 latency exceeds 1s",
        severity=AlertSeverity.WARNING,
        condition='histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="agentforge-backend"}[5m])) by (le)) > 1',
        for_duration="10m",
        labels={"team": "platform", "service": "api"},
        annotations={"summary": "High API latency", "runbook": "https://runbooks.agentforge.com/high-latency"},
    ),
    AlertRule(
        name="WorkflowFailureRate",
        description="Workflow failure rate exceeds 5%",
        severity=AlertSeverity.WARNING,
        condition='sum(rate(workflow_completed_total{status="failed"}[5m])) / sum(rate(workflow_completed_total[5m])) > 0.05',
        for_duration="15m",
        labels={"team": "platform", "service": "workflow"},
        annotations={"summary": "High workflow failure rate", "runbook": "https://runbooks.agentforge.com/workflow-failures"},
    ),
    AlertRule(
        name="DeploymentFailureRate",
        description="Deployment failure rate exceeds 1%",
        severity=AlertSeverity.CRITICAL,
        condition='sum(rate(deployment_completed_total{status="failed"}[5m])) / sum(rate(deployment_completed_total[5m])) > 0.01',
        for_duration="5m",
        labels={"team": "platform", "service": "deployment"},
        annotations={"summary": "High deployment failure rate", "runbook": "https://runbooks.agentforge.com/deployment-failures"},
    ),
    AlertRule(
        name="HighAgentFailureRate",
        description="Agent execution failure rate exceeds 10%",
        severity=AlertSeverity.WARNING,
        condition='sum(rate(agent_execution_completed_total{status="failed"}[5m])) / sum(rate(agent_execution_completed_total[5m])) > 0.1',
        for_duration="15m",
        labels={"team": "platform", "service": "agents"},
        annotations={"summary": "High agent failure rate", "runbook": "https://runbooks.agentforge.com/agent-failures"},
    ),
    AlertRule(
        name="HighCpuUsage",
        description="CPU usage exceeds 80%",
        severity=AlertSeverity.WARNING,
        condition='sum(rate(container_cpu_usage_seconds_total{namespace="agentforge"}[5m])) / sum(container_spec_cpu_quota/container_spec_cpu_period{namespace="agentforge"}) > 0.8',
        for_duration="15m",
        labels={"team": "platform", "resource": "cpu"},
        annotations={"summary": "High CPU usage", "runbook": "https://runbooks.agentforge.com/high-cpu"},
    ),
    AlertRule(
        name="HighMemoryUsage",
        description="Memory usage exceeds 85%",
        severity=AlertSeverity.WARNING,
        condition='sum(container_memory_usage_bytes{namespace="agentforge"}) / sum(container_spec_memory_limit_bytes{namespace="agentforge"}) > 0.85',
        for_duration="15m",
        labels={"team": "platform", "resource": "memory"},
        annotations={"summary": "High memory usage", "runbook": "https://runbooks.agentforge.com/high-memory"},
    ),
    AlertRule(
        name="DiskSpaceLow",
        description="Disk space below 10%",
        severity=AlertSeverity.CRITICAL,
        condition='(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1',
        for_duration="5m",
        labels={"team": "platform", "resource": "disk"},
        annotations={"summary": "Low disk space", "runbook": "https://runbooks.agentforge.com/low-disk"},
    ),
]


# Global instances
slo_monitor = SLOMonitor()
slo_reporter = SLOReporter(slo_monitor)


async def initialize_slo_monitoring():
    """Initialize SLO monitoring with defaults."""
    # Register SLIs
    for sli in DEFAULT_SLIS.values():
        slo_monitor.register_sli(sli)
    
    # Register SLO targets
    for target in DEFAULT_SLO_TARGETS.values():
        slo_monitor.register_slo(target)
    
    # Register alert rules
    for rule in DEFAULT_ALERT_RULES:
        slo_monitor.register_alert_rule(rule)
    
    # Add notification channels (configured via environment)
    # slo_monitor.add_notification_channel(NotificationChannel(
    #     name="slack-critical",
    #     type="slack",
    #     config={"webhook_url": settings.SLACK_WEBHOOK_URL},
    #     severity_filter=["critical"],
    # ))
    
    return slo_monitor


async def get_slo_dashboard(service_name: str = "agentforge") -> Dict[str, Any]:
    """Get SLO dashboard data."""
    dashboard = await slo_monitor.get_dashboard(service_name)
    return dashboard.model_dump()


async def check_slo_compliance() -> Dict[str, Any]:
    """Check SLO compliance and return report."""
    return await slo_reporter.generate_report(
        period_start=datetime.now(timezone.utc) - timedelta(days=30),
        period_end=datetime.now(timezone.utc),
    )
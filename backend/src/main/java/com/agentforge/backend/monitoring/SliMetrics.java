package com.agentforge.backend.monitoring;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

@Component
@RequiredArgsConstructor
public class SliMetrics {

    private final MeterRegistry meterRegistry;

    private final Counter httpRequestsTotal;
    private final Counter httpErrorsTotal;
    private final Timer httpRequestDuration;
    private final Counter workflowExecutionsTotal;
    private final Counter workflowFailuresTotal;
    private final Timer workflowDuration;
    private final Counter agentExecutionsTotal;
    private final Counter agentFailuresTotal;
    private final Timer agentDuration;
    private final Counter deploymentsTotal;
    private final Counter deploymentFailuresTotal;
    private final Timer deploymentDuration;

    public SliMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;

        this.httpRequestsTotal = Counter.builder("http_requests_total")
                .description("Total HTTP requests")
                .register(meterRegistry);

        this.httpErrorsTotal = Counter.builder("http_errors_total")
                .description("Total HTTP errors")
                .register(meterRegistry);

        this.httpRequestDuration = Timer.builder("http_request_duration_seconds")
                .description("HTTP request latency")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);

        this.workflowExecutionsTotal = Counter.builder("workflow_executions_total")
                .description("Total workflow executions")
                .register(meterRegistry);

        this.workflowFailuresTotal = Counter.builder("workflow_failures_total")
                .description("Total workflow failures")
                .register(meterRegistry);

        this.workflowDuration = Timer.builder("workflow_duration_seconds")
                .description("Workflow execution duration")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);

        this.agentExecutionsTotal = Counter.builder("agent_executions_total")
                .description("Total agent executions")
                .register(meterRegistry);

        this.agentFailuresTotal = Counter.builder("agent_failures_total")
                .description("Total agent failures")
                .register(meterRegistry);

        this.agentDuration = Timer.builder("agent_duration_seconds")
                .description("Agent execution duration")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);

        this.deploymentsTotal = Counter.builder("deployments_total")
                .description("Total deployments")
                .register(meterRegistry);

        this.deploymentFailuresTotal = Counter.builder("deployment_failures_total")
                .description("Total deployment failures")
                .register(meterRegistry);

        this.deploymentDuration = Timer.builder("deployment_duration_seconds")
                .description("Deployment duration")
                .publishPercentiles(0.5, 0.95, 0.99)
                .register(meterRegistry);
    }

    public void recordHttpRequest(String method, String endpoint, int status, Duration duration) {
        httpRequestsTotal.increment();
        if (status >= 400) {
            httpErrorsTotal.increment();
        }
        httpRequestDuration.record(duration);
    }

    public <T> T recordHttpRequest(String method, String endpoint, Supplier<T> supplier) {
        return httpRequestDuration.record(supplier);
    }

    public void recordWorkflowExecution(String workflowType, boolean success, Duration duration) {
        workflowExecutionsTotal.increment();
        if (!success) {
            workflowFailuresTotal.increment();
        }
        workflowDuration.record(duration);
    }

    public void recordAgentExecution(String agentRole, boolean success, Duration duration) {
        agentExecutionsTotal.increment();
        if (!success) {
            agentFailuresTotal.increment();
        }
        agentDuration.record(duration);
    }

    public void recordDeployment(String environment, boolean success, Duration duration) {
        deploymentsTotal.increment();
        if (!success) {
            deploymentFailuresTotal.increment();
        }
        deploymentDuration.record(duration);
    }

    // SLO evaluation helpers
    public double getApiAvailability() {
        // This would query Prometheus in production
        // For now, return a computed value based on counters
        double total = httpRequestsTotal.count();
        double errors = httpErrorsTotal.count();
        return total > 0 ? 1.0 - (errors / total) : 1.0;
    }

    public double getApiLatencyP99() {
        // Would query histogram in Prometheus
        return httpRequestDuration.percentile(0.99, TimeUnit.MILLISECONDS);
    }

    public double getWorkflowSuccessRate() {
        double total = workflowExecutionsTotal.count();
        double failures = workflowFailuresTotal.count();
        return total > 0 ? 1.0 - (failures / total) : 1.0;
    }

    public double getDeploymentSuccessRate() {
        double total = deploymentsTotal.count();
        double failures = deploymentFailuresTotal.count();
        return total > 0 ? 1.0 - (failures / total) : 1.0;
    }
}
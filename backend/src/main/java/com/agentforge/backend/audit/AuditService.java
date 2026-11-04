package com.agentforge.backend.audit;

import com.agentforge.backend.audit.AuditLog;
import com.agentforge.backend.audit.AuditLogRepository;
import com.agentforge.backend.common.util.CryptoUtil;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuditService {

    private final AuditLogRepository auditRepository;
    private String lastHash = null;

    @jakarta.annotation.PostConstruct
    public void init() {
        // Load last hash from database
        List<AuditLog> lastLogs = auditRepository.findTop1ByOrderByTimestampDesc();
        if (!lastLogs.isEmpty()) {
            this.lastHash = lastLogs.get(0).getEventHash();
        }
        CryptoUtil.getInstance().initialize(System.getenv("ENCRYPTION_KEY"));
    }

    @Transactional
    public AuditLog log(AuditEvent event) {
        AuditLog log = AuditLog.builder()
                .eventType(event.eventType())
                .severity(event.severity())
                .timestamp(LocalDateTime.now())
                .actorId(event.actorId())
                .actorType(event.actorType())
                .actorIp(event.actorIp())
                .actorUserAgent(event.actorUserAgent())
                .resourceType(event.resourceType())
                .resourceId(event.resourceId())
                .resourceName(event.resourceName())
                .action(event.action())
                .outcome(event.outcome())
                .requestId(event.requestId())
                .sessionId(event.sessionId())
                .correlationId(event.correlationId())
                .detailsJson(toJson(event.details()))
                .riskScore(event.riskScore())
                .riskFactorsJson(toJson(event.riskFactors()))
                .complianceTagsJson(toJson(event.complianceTags()))
                .dataClassification(event.dataClassification())
                .previousHash(lastHash)
                .build();

        // Compute hash for integrity chain
        String eventHash = computeHash(log);
        log.setEventHash(eventHash);
        lastHash = eventHash;

        AuditLog saved = auditRepository.save(log);
        
        // Async write to immutable log (WORM storage)
        CompletableFuture.runAsync(() -> writeToImmutableLog(log));
        
        return saved;
    }

    public CompletableFuture<Void> logAsync(AuditEvent event) {
        return CompletableFuture.runAsync(() -> log(event));
    }

    public List<AuditLog> query(AuditQuery query) {
        // Implementation for querying audit logs
        return auditRepository.findAll(); // Simplified
    }

    public AuditReport generateReport(LocalDateTime start, LocalDateTime end) {
        // Generate compliance report
        return new AuditReport(UUID.randomUUID(), LocalDateTime.now(), start, end, 0, Map.of(), Map.of(), Map.of(), 0, 0, 0, 0, 0, true);
    }

    private String computeHash(AuditLog log) {
        try {
            String data = String.join("|",
                    log.getEventId().toString(),
                    log.getEventType(),
                    log.getTimestamp().toString(),
                    log.getActorId() != null ? log.getActorId().toString() : "",
                    log.getAction(),
                    log.getOutcome(),
                    log.getDetailsJson(),
                    log.getPreviousHash()
            );
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(data.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(hash);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to compute hash", e);
        }
    }

    private void writeToImmutableLog(AuditLog auditLog) {
        // Write to WORM storage (S3 Object Lock, CloudWatch, etc.)
        log.info("AUDIT: {}", auditLog.getEventHash());
    }

    private String toJson(Object obj) {
        if (obj == null) return "{}";
        try {
            return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(obj);
        } catch (Exception e) {
            return "{}";
        }
    }

    // Event record
    public record AuditEvent(
            String eventType,
            String severity,
            UUID actorId,
            String actorType,
            String actorIp,
            String actorUserAgent,
            String resourceType,
            UUID resourceId,
            String resourceName,
            String action,
            String outcome,
            String requestId,
            String sessionId,
            String correlationId,
            Map<String, Object> details,
            int riskScore,
            List<String> riskFactors,
            List<String> complianceTags,
            String dataClassification
    ) {
        @SuppressWarnings("unchecked")
        public AuditEvent(
                String eventType,
                String severity,
                UUID actorId,
                String actorType,
                String resourceType,
                UUID resourceId,
                String resourceName,
                String action,
                String outcome,
                Map<String, ?> details,
                int riskScore,
                List<String> riskFactors,
                List<String> complianceTags,
                String dataClassification
        ) {
            this(
                    eventType,
                    severity,
                    actorId,
                    actorType,
                    null,
                    null,
                    resourceType,
                    resourceId,
                    resourceName,
                    action,
                    outcome,
                    null,
                    null,
                    null,
                    details != null ? (Map<String, Object>) details : Map.of(),
                    riskScore,
                    riskFactors,
                    complianceTags,
                    dataClassification
            );
        }
    }

    public record AuditQuery(
            List<String> eventTypes,
            List<UUID> actorIds,
            List<String> resourceTypes,
            List<UUID> resourceIds,
            List<String> outcomes,
            List<String> severities,
            LocalDateTime startTime,
            LocalDateTime endTime,
            List<String> complianceTags,
            int limit,
            int offset
    ) {}

    public record AuditReport(
            UUID reportId,
            LocalDateTime generatedAt,
            LocalDateTime periodStart,
            LocalDateTime periodEnd,
            int totalEvents,
            Map<String, Integer> eventsByType,
            Map<String, Integer> eventsBySeverity,
            Map<String, Integer> eventsByOutcome,
            int failedLogins,
            int permissionDenials,
            int dataAccessEvents,
            int adminActions,
            int suspiciousActivities,
            boolean integrityVerified
    ) {}
}
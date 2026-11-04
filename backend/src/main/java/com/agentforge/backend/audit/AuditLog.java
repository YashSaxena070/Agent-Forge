package com.agentforge.backend.audit;

import com.agentforge.backend.common.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "audit_logs",
        indexes = {
                @Index(name = "idx_audit_timestamp", columnList = "timestamp"),
                @Index(name = "idx_audit_actor", columnList = "actor_id"),
                @Index(name = "idx_audit_resource", columnList = "resource_type, resource_id"),
                @Index(name = "idx_audit_event_type", columnList = "event_type"),
                @Index(name = "idx_audit_compliance", columnList = "compliance_tags")
        })
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AuditLog extends BaseEntity {

    @Id
    @GeneratedValue
    @Column(name = "event_id", columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID eventId;

    @Column(name = "event_type", nullable = false, length = 100)
    private String eventType;

    @Column(name = "severity", nullable = false, length = 20)
    private String severity;

    @Column(name = "timestamp", nullable = false, columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private LocalDateTime timestamp;

    @Column(name = "actor_id", columnDefinition = "uuid")
    private UUID actorId;

    @Column(name = "actor_type", nullable = false, length = 50)
    private String actorType;

    @Column(name = "actor_ip", length = 45)
    private String actorIp;

    @Column(name = "actor_user_agent", columnDefinition = "TEXT")
    private String actorUserAgent;

    @Column(name = "resource_type", length = 100)
    private String resourceType;

    @Column(name = "resource_id", columnDefinition = "uuid")
    private UUID resourceId;

    @Column(name = "resource_name", length = 255)
    private String resourceName;

    @Column(name = "action", nullable = false, length = 100)
    private String action;

    @Column(name = "outcome", nullable = false, length = 20)
    private String outcome;

    @Column(name = "request_id", length = 255)
    private String requestId;

    @Column(name = "session_id", length = 255)
    private String sessionId;

    @Column(name = "correlation_id", length = 255)
    private String correlationId;

    @Column(name = "details", columnDefinition = "jsonb")
    private String detailsJson;

    @Column(name = "risk_score")
    private int riskScore = 0;

    @Column(name = "risk_factors", columnDefinition = "jsonb")
    private String riskFactorsJson;

    @Column(name = "compliance_tags", columnDefinition = "jsonb")
    private String complianceTagsJson;

    @Column(name = "data_classification", length = 50)
    private String dataClassification;

    @Column(name = "previous_hash", length = 64)
    private String previousHash;

    @Column(name = "event_hash", length = 64, unique = true)
    private String eventHash;
}
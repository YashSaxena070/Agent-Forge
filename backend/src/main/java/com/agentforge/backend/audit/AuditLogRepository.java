package com.agentforge.backend.audit;

import com.agentforge.backend.audit.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public interface AuditLogRepository extends JpaRepository<AuditLog, UUID> {

    List<AuditLog> findTop1ByOrderByTimestampDesc();

    @Query("SELECT a FROM AuditLog a WHERE a.timestamp >= :start AND a.timestamp <= :end ORDER BY a.timestamp DESC")
    List<AuditLog> findByTimestampBetween(
            @Param("start") LocalDateTime start,
            @Param("end") LocalDateTime end);

    @Query("SELECT a FROM AuditLog a WHERE a.actorId = :actorId ORDER BY a.timestamp DESC")
    List<AuditLog> findByActorId(@Param("actorId") UUID actorId);

    @Query("SELECT a FROM AuditLog a WHERE a.resourceType = :type AND a.resourceId = :id ORDER BY a.timestamp DESC")
    List<AuditLog> findByResource(@Param("type") String type, @Param("id") UUID id);

    @Query("SELECT a FROM AuditLog a WHERE a.eventType = :type ORDER BY a.timestamp DESC")
    List<AuditLog> findByEventType(@Param("type") String type);

    @Query("SELECT a FROM AuditLog a WHERE :tags MEMBER OF a.complianceTagsJson ORDER BY a.timestamp DESC")
    List<AuditLog> findByComplianceTag(@Param("tags") String tag);
}
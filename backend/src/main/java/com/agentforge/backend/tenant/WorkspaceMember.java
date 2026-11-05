package com.agentforge.backend.tenant;

import com.agentforge.backend.common.entity.BaseEntity;
import com.agentforge.backend.domain.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "workspace_members",
        uniqueConstraints = {
                @UniqueConstraint(columnNames = {"workspace_id", "user_id"})
        })
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkspaceMember extends BaseEntity {

    @Id
    @GeneratedValue
    @Column(name = "id", columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "workspace_id", nullable = false)
    private Workspace workspace;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false, length = 20)
    private MemberRole role;

    @Column(name = "status", length = 20)
    @Builder.Default
    private String status = "active";

    @Column(name = "custom_permissions", columnDefinition = "jsonb")
    @Builder.Default
    private String customPermissionsJson = "[]";

    @Column(name = "joined_at", nullable = false)
    @Builder.Default
    private LocalDateTime joinedAt = LocalDateTime.now();

    @Column(name = "invited_by", columnDefinition = "uuid")
    private UUID invitedBy;

    @Column(name = "last_active_at")
    private LocalDateTime lastActiveAt;
}
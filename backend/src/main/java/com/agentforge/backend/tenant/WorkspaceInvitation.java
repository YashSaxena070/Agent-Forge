package com.agentforge.backend.tenant;

import com.agentforge.backend.common.entity.BaseEntity;
import com.agentforge.backend.domain.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "workspace_invitations",
        uniqueConstraints = {
                @UniqueConstraint(columnNames = {"workspace_id", "email"})
        })
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkspaceInvitation extends BaseEntity {

    @Id
    @GeneratedValue
    @Column(name = "id", columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "workspace_id", nullable = false)
    private Workspace workspace;

    @Column(name = "email", nullable = false, length = 255)
    private String email;

    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false, length = 20)
    private MemberRole role;

    @Column(name = "token", unique = true, nullable = false, length = 255)
    private String token;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 20)
    @Builder.Default
    private String status = "pending";

    @Column(name = "accepted_at")
    private LocalDateTime acceptedAt;

    @Column(name = "accepted_by", columnDefinition = "uuid")
    private UUID acceptedBy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "invited_by", nullable = false)
    private User invitedByUser;

    public boolean isExpired() {
        return LocalDateTime.now().isAfter(expiresAt);
    }

    public boolean isPending() {
        return "pending".equals(status) && !isExpired();
    }
}
package com.agentforge.backend.domain.organization;

import com.agentforge.backend.common.entity.BaseEntity;
import com.agentforge.backend.common.enums.InvitationStatus;
import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.domain.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(
        name = "organization_invitations",
        indexes = {
                @Index(
                        name = "idx_org_invitation_token",
                        columnList = "token"
                ),
                @Index(
                        name = "idx_org_invitation_email",
                        columnList = "email"
                ),
                @Index(
                        name = "idx_org_invitation_organization",
                        columnList = "organization_id"
                )
        }
)
public class OrganizationInvitation
        extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "organization_id",
            nullable = false
    )
    private Organization organization;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "invited_by",
            nullable = false
    )
    private User invitedBy;

    @Column(
            nullable = false,
            length = 320
    )
    private String email;

    @Column(
            nullable = false,
            unique = true,
            length = 512
    )
    private String token;

    @Enumerated(EnumType.STRING)
    @Column(
            nullable = false,
            length = 30
    )
    private OrganizationRole role;

    @Enumerated(EnumType.STRING)
    @Column(
            nullable = false,
            length = 30
    )
    @Builder.Default
    private InvitationStatus status =
            InvitationStatus.PENDING;

    @Column(nullable = false)
    private LocalDateTime expiresAt;

    private LocalDateTime acceptedAt;
}
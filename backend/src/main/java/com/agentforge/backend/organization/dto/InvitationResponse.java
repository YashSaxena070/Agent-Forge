package com.agentforge.backend.organization.dto;

import com.agentforge.backend.common.enums.InvitationStatus;
import com.agentforge.backend.common.enums.OrganizationRole;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record InvitationResponse(

        UUID id,

        UUID organizationId,

        String organizationName,

        String email,

        OrganizationRole role,

        InvitationStatus status,

        LocalDateTime expiresAt,

        String invitationToken

) {
}
package com.agentforge.backend.organization.dto;

import com.agentforge.backend.common.enums.OrganizationRole;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record MemberResponse(

        UUID id,

        UUID userId,

        String fullName,

        String email,

        OrganizationRole role,

        boolean emailVerified,

        LocalDateTime joinedAt

) {
}
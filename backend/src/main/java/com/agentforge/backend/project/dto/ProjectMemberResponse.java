package com.agentforge.backend.project.dto;

import com.agentforge.backend.common.enums.ProjectRole;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record ProjectMemberResponse(

        UUID id,

        UUID userId,

        String fullName,

        String email,

        ProjectRole role,

        LocalDateTime joinedAt

) {
}
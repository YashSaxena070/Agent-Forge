package com.agentforge.backend.project.dto;

import com.agentforge.backend.common.enums.ProjectStatus;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record ProjectResponse(

        UUID id,

        UUID organizationId,

        String name,

        String slug,

        String description,

        ProjectStatus status,

        LocalDateTime createdAt,

        LocalDateTime updatedAt

) {
}
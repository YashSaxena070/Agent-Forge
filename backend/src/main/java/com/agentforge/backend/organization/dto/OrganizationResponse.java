package com.agentforge.backend.organization.dto;

import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record OrganizationResponse (

        UUID id,

        String name,

        String slug,

        String description,

        String logoUrl,

        LocalDateTime createdAt,

        LocalDateTime updatedAt

) {
}
package com.agentforge.backend.auth.dto;

import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record SessionResponse(

        UUID id,

        String deviceName,

        String deviceType,

        String ipAddress,

        String userAgent,

        LocalDateTime createdAt,

        LocalDateTime lastUsedAt,

        LocalDateTime expiresAt,

        boolean current

) {
}
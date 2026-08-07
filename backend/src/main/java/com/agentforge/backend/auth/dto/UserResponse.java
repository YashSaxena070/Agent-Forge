package com.agentforge.backend.auth.dto;

import com.agentforge.backend.common.enums.SystemRole;
import com.agentforge.backend.common.enums.UserStatus;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Builder
public record UserResponse(

        UUID id,

        String fullName,

        String email,

        UserStatus status,

        SystemRole systemRole,

        boolean emailVerified,

        LocalDateTime createdAt

) {
}
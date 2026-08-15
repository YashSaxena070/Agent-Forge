package com.agentforge.backend.project.dto;

import com.agentforge.backend.common.enums.ProjectRole;
import jakarta.validation.constraints.NotNull;

import java.util.UUID;

public record AddProjectMemberRequest(

        @NotNull(
                message = "User ID is required."
        )
        UUID userId,

        @NotNull(
                message = "Project role is required."
        )
        ProjectRole role

) {
}
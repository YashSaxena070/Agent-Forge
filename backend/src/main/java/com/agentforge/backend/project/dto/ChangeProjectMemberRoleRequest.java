package com.agentforge.backend.project.dto;

import com.agentforge.backend.common.enums.ProjectRole;
import jakarta.validation.constraints.NotNull;

public record ChangeProjectMemberRoleRequest(

        @NotNull(
                message = "Project role is required."
        )
        ProjectRole role

) {
}
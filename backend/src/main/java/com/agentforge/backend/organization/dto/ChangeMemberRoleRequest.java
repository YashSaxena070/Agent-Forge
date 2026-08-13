package com.agentforge.backend.organization.dto;

import com.agentforge.backend.common.enums.OrganizationRole;
import jakarta.validation.constraints.NotNull;

public record ChangeMemberRoleRequest(

        @NotNull(message = "Role is required.")
        OrganizationRole role

) {
}
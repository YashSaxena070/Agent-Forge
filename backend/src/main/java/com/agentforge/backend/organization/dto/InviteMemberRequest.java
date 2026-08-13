package com.agentforge.backend.organization.dto;

import com.agentforge.backend.common.enums.OrganizationRole;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record InviteMemberRequest(

        @NotBlank(message = "Email is required.")
        @Email(message = "Please provide a valid email.")
        String email,

        @NotNull(message = "Organization role is required.")
        OrganizationRole role

) {
}
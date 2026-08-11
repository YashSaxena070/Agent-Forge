package com.agentforge.backend.organization.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateOrganizationRequest(

        @NotBlank(message = "Organization name is required.")
        @Size(
                min = 2,
                max = 100,
                message = "Organization name must be between 2 and 100 characters."
        )
        String name,

        @Size(
                max = 500,
                message = "Description cannot exceed 500 characters."
        )
        String description,

        @Size(
                max = 255,
                message = "Logo URL cannot exceed 255 characters."
        )
        String logoUrl

) {
}
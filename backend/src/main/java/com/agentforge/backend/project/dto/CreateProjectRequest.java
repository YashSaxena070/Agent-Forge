package com.agentforge.backend.project.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateProjectRequest(

        @NotBlank(
                message = "Project name is required."
        )
        @Size(
                min = 2,
                max = 100,
                message = "Project name must be between 2 and 100 characters."
        )
        String name,

        @Size(
                max = 1000,
                message = "Description cannot exceed 1000 characters."
        )
        String description

) {
}
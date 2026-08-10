package com.agentforge.backend.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

public record LoginRequest(

        @NotBlank(message = "Email is required.")
        @Email(message = "Please provide a valid email.")
        String email,

        @NotBlank(message = "Password is required.")
        String password

) {
}

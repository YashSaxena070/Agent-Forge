package com.agentforge.backend.organization.dto;

import jakarta.validation.constraints.NotNull;

import java.util.UUID;

public record TransferOwnershipRequest(

        @NotNull(message = "New owner member ID is required.")
        UUID memberId

) {
}
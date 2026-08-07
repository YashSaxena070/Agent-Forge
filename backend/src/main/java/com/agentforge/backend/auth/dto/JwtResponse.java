package com.agentforge.backend.auth.dto;

import lombok.Builder;

@Builder
public record JwtResponse(

        String accessToken,

        String refreshToken,

        String tokenType,

        long expiresIn

) {
}
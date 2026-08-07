package com.agentforge.backend.security.jwt;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "jwt")
public record JwtProperties(

        String secret,

        Long accessTokenExpiration,

        Long refreshTokenExpiration

) {
}
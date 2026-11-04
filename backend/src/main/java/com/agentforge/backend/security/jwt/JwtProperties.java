package com.agentforge.backend.security.jwt;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "jwt")
public record JwtProperties(

        String secret,

        String rsaPrivateKey,

        String rsaPublicKey,

        Long accessTokenExpiration,

        Long refreshTokenExpiration,

        String algorithm,

        String issuer,

        String audience
) {
    public String getAlgorithm() {
        return algorithm != null ? algorithm : "RS256";
    }

    public String getIssuer() {
        return issuer != null ? issuer : "agentforge";
    }

    public String getAudience() {
        return audience != null ? audience : "agentforge-api";
    }
}
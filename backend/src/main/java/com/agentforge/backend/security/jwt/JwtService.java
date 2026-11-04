package com.agentforge.backend.security.jwt;

import com.agentforge.backend.domain.user.User;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.source.ImmutableJWKSet;
import com.nimbusds.jose.jwk.source.JWKSource;
import com.nimbusds.jose.proc.SecurityContext;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
import org.springframework.stereotype.Service;

import com.nimbusds.jose.jwk.JWKSet;

import javax.crypto.SecretKey;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

@Service
@RequiredArgsConstructor
public class JwtService {

    private final JwtProperties properties;
    private final JWKSource<SecurityContext> jwkSource;
    private final JwtDecoder jwtDecoder;

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public <T> T extractClaim(String token, Function<Claims, T> resolver) {
        Claims claims = extractAllClaims(token);
        return resolver.apply(claims);
    }

    public String generateAccessToken(User user) {
        Map<String, Object> claims = new HashMap<>();

        claims.put("userId", user.getId().toString());
        claims.put("role", user.getSystemRole().name());
        claims.put("permissions", user.getSystemRole().getPermissions());

        return generateToken(claims, user.getEmail(), properties.accessTokenExpiration());
    }

    public String generateRefreshToken(User user) {
        return generateToken(new HashMap<>(), user.getEmail(), properties.refreshTokenExpiration());
    }

    private String generateToken(Map<String, Object> claims, String subject, Long expiration) {
        return Jwts.builder()
                .claims(claims)
                .id(UUID.randomUUID().toString())
                .subject(subject)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expiration))
                .issuer(properties.issuer())
                .audience().add(properties.audience()).and()
                .signWith(getSigningKey())
                .compact();
    }

    public boolean isTokenValid(String token, String email) {
        try {
            return extractUsername(token).equals(email) && !isTokenExpired(token);
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isTokenValid(String token) {
        try {
            extractAllClaims(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    private Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    private SecretKey getSigningKey() {
        byte[] keyBytes = Decoders.BASE64.decode(properties.secret());
        return Keys.hmacShaKeyFor(keyBytes);
    }

    public JwtDecoder jwtDecoder() {
        return jwtDecoder;
    }

    public Map<String, Object> parseToken(String token) {
        Claims claims = extractAllClaims(token);
        Map<String, Object> result = new HashMap<>();
        claims.forEach(result::put);
        return result;
    }
}
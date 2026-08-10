package com.agentforge.backend.security.jwt;

import com.agentforge.backend.domain.user.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

@Service
@RequiredArgsConstructor
public class JwtService {

    private final JwtProperties properties;

    public String extractUsername(String token) {

        return extractClaim(
                token,
                Claims::getSubject
        );

    }

    public <T> T extractClaim(

            String token,

            Function<Claims, T> resolver

    ) {

        Claims claims = extractAllClaims(token);

        return resolver.apply(claims);

    }

    public String generateAccessToken(User user) {

        Map<String, Object> claims = new HashMap<>();

        claims.put("userId", user.getId().toString());

        claims.put("role", user.getSystemRole().name());

        return generateToken(
                claims,
                user.getEmail(),
                properties.accessTokenExpiration()
        );

    }

    public String generateRefreshToken(User user) {

        return generateToken(
                new HashMap<>(),
                user.getEmail(),
                properties.refreshTokenExpiration()
        );

    }

    private String generateToken(
            Map<String, Object> claims,
            String subject,
            Long expiration
    ) {

        return Jwts.builder()
                .claims(claims)
                .id(UUID.randomUUID().toString())
                .subject(subject)
                .issuedAt(new Date())
                .expiration(
                        new Date(
                                System.currentTimeMillis()
                                        + expiration
                        )
                )
                .signWith(getSigningKey())
                .compact();
    }

    public boolean isTokenValid(

            String token,

            String email

    ) {

        return extractUsername(token).equals(email)

                &&

                !isTokenExpired(token);

    }

    public boolean isTokenValid(String token) {

        try {

            extractAllClaims(token);

            return true;

        } catch (Exception exception) {

            return false;
        }
    }

    private boolean isTokenExpired(

            String token

    ) {

        return extractExpiration(token)

                .before(new Date());

    }

    private Date extractExpiration(

            String token

    ) {

        return extractClaim(

                token,

                Claims::getExpiration

        );

    }

    private Claims extractAllClaims(

            String token

    ) {

        return Jwts.parser()

                .verifyWith(getSigningKey())

                .build()

                .parseSignedClaims(token)

                .getPayload();

    }

    private SecretKey getSigningKey() {

        byte[] keyBytes = Decoders.BASE64.decode(

                properties.secret()

        );

        return Keys.hmacShaKeyFor(keyBytes);

    }

}
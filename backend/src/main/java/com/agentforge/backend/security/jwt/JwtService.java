package com.agentforge.backend.security.jwt;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.util.Date;
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

    public String generateAccessToken(String email) {

        return Jwts.builder()

                .subject(email)

                .issuedAt(new Date())

                .expiration(new Date(

                        System.currentTimeMillis()
                                + properties.accessTokenExpiration()

                ))

                .signWith(getSigningKey())

                .compact();

    }

    public String generateRefreshToken(String email) {

        return Jwts.builder()

                .subject(email)

                .issuedAt(new Date())

                .expiration(new Date(

                        System.currentTimeMillis()
                                + properties.refreshTokenExpiration()

                ))

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
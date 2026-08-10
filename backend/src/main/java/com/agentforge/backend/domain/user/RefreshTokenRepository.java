package com.agentforge.backend.domain.user;

import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface RefreshTokenRepository
        extends JpaRepository<RefreshToken, UUID> {

    Optional<RefreshToken> findByToken(String token);

    List<RefreshToken> findByUser(User user);
    List<RefreshToken> findAllByUser(User user);

    List<RefreshToken> findAllByUserAndRevokedFalse(User user);

    Optional<RefreshToken> findByTokenAndRevokedFalse(String token);

    List<RefreshToken> findAllByExpiresAtBefore(
            LocalDateTime dateTime
    );

}
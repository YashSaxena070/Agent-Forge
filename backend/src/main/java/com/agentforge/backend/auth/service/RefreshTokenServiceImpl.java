package com.agentforge.backend.auth.service;

import com.agentforge.backend.auth.exception.InvalidRefreshTokenException;
import com.agentforge.backend.auth.exception.RefreshTokenReuseException;
import com.agentforge.backend.domain.user.RefreshToken;
import com.agentforge.backend.domain.user.RefreshTokenRepository;
import com.agentforge.backend.domain.user.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class RefreshTokenServiceImpl
                implements RefreshTokenService {

        private final RefreshTokenRepository refreshTokenRepository;

        @Override
        @Transactional
        public void revokeToken(String token) {

                RefreshToken refreshToken = refreshTokenRepository
                                .findByToken(token)
                                .orElse(null);

                if (refreshToken == null) {
                        return;
                }

                if (refreshToken.isRevoked()) {
                        return;
                }

                refreshToken.setRevoked(true);

                refreshTokenRepository.save(refreshToken);
        }

        @Override
        @Transactional
        public void revokeAllTokens(User user) {

                List<RefreshToken> tokens = refreshTokenRepository
                                .findAllByUserAndRevokedFalse(user);

                for (RefreshToken token : tokens) {
                        token.setRevoked(true);
                }

                refreshTokenRepository.saveAll(tokens);
        }

        @Override
        @Transactional(readOnly = true)
        public List<RefreshToken> getActiveTokens(User user) {

                return refreshTokenRepository
                                .findAllByUserAndRevokedFalse(user);
        }

        @Override
        @Transactional(readOnly = true)
        public RefreshToken findToken(String token) {

                return refreshTokenRepository
                                .findByToken(token)
                                .orElseThrow(() -> new InvalidRefreshTokenException(
                                                "Invalid refresh token."));
        }

        @Override
        @Transactional(noRollbackFor = { RefreshTokenReuseException.class, InvalidRefreshTokenException.class })
        public RefreshToken findValidToken(String token) {

                RefreshToken refreshToken = refreshTokenRepository
                                .findByToken(token)
                                .orElseThrow(() -> new InvalidRefreshTokenException(
                                                "Invalid refresh token."));

                if (refreshToken.isRevoked()) {

                        User user = refreshToken.getUser();

                        List<RefreshToken> activeTokens = refreshTokenRepository
                                        .findAllByUserAndRevokedFalse(user);

                        for (RefreshToken activeToken : activeTokens) {

                                activeToken.setRevoked(true);
                        }

                        refreshTokenRepository.saveAll(activeTokens);

                        throw new RefreshTokenReuseException(
                                        "Refresh token reuse detected.");
                }

                if (refreshToken.getExpiresAt()
                                .isBefore(LocalDateTime.now())) {

                        refreshToken.setRevoked(true);

                        refreshTokenRepository.save(refreshToken);

                        throw new InvalidRefreshTokenException(
                                        "Refresh token has expired.");
                }

                return refreshToken;
        }
}
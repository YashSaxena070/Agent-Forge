package com.agentforge.backend.auth.service;

import com.agentforge.backend.domain.user.RefreshToken;
import com.agentforge.backend.domain.user.User;

import java.util.List;

public interface RefreshTokenService {

    void revokeToken(String token);

    void revokeAllTokens(User user);

    List<RefreshToken> getActiveTokens(User user);

    RefreshToken findValidToken(String token);

    RefreshToken findToken(String token);
}
package com.agentforge.backend.auth.service;

import com.agentforge.backend.auth.dto.*;
import com.agentforge.backend.domain.user.User;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.transaction.Transactional;

public interface AuthService {

    UserResponse register(RegisterRequest request);

    JwtResponse login(LoginRequest request,
                      HttpServletRequest httpRequest);

    void logout(LogoutRequest request);

    void logoutAll(User user);

    JwtResponse refresh(
            RefreshTokenRequest request,
            HttpServletRequest httpRequest
    );


}
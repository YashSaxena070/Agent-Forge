package com.agentforge.backend.auth.service;

import com.agentforge.backend.auth.dto.JwtResponse;
import com.agentforge.backend.auth.dto.LoginRequest;
import com.agentforge.backend.auth.dto.RegisterRequest;
import com.agentforge.backend.auth.dto.UserResponse;

public interface AuthService {

    UserResponse register(RegisterRequest request);

    JwtResponse login(LoginRequest request);

}
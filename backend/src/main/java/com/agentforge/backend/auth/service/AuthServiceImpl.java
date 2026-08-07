package com.agentforge.backend.auth.service;

import com.agentforge.backend.auth.dto.JwtResponse;
import com.agentforge.backend.auth.dto.LoginRequest;
import com.agentforge.backend.auth.dto.RegisterRequest;
import com.agentforge.backend.auth.dto.UserResponse;
import com.agentforge.backend.auth.exception.EmailAlreadyExistsException;
import com.agentforge.backend.auth.mapper.AuthMapper;
import com.agentforge.backend.common.enums.SystemRole;
import com.agentforge.backend.common.enums.UserStatus;
import com.agentforge.backend.domain.user.RefreshToken;
import com.agentforge.backend.domain.user.RefreshTokenRepository;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.domain.user.UserRepository;
import com.agentforge.backend.security.jwt.JwtService;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthMapper authMapper;
    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;
    private final RefreshTokenRepository refreshTokenRepository;

    @Override
    public UserResponse register(RegisterRequest request) {

        if (userRepository.existsByEmail(request.getEmail())) {
            throw new EmailAlreadyExistsException(
                    "Email already registered."
            );
        }

        User user = authMapper.toEntity(request);
        user.setPassword(
                passwordEncoder.encode(request.getPassword())
        );
        user.setStatus(UserStatus.ACTIVE);
        user.setSystemRole(SystemRole.USER);
        user.setEmailVerified(false);
        User savedUser = userRepository.save(user);

        return authMapper.toUserResponse(savedUser);
    }

    @Override
    @Transactional
    public JwtResponse login(LoginRequest request) {

        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getEmail(),
                        request.getPassword()
                )
        );

        User user = userRepository
                .findByEmail(request.getEmail())
                .orElseThrow();

        refreshTokenRepository.deleteByUser(user);

        String accessToken = jwtService.generateAccessToken(user);

        String refreshToken = jwtService.generateRefreshToken(user);

        RefreshToken entity = RefreshToken.builder()
                .token(refreshToken)
                .user(user)
                .expiresAt(
                        LocalDateTime.now()
                                .plusDays(7)
                )
                .revoked(false)
                .build();

        refreshTokenRepository.save(entity);

        return JwtResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(900L)
                .build();

    }
}
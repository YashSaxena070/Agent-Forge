package com.agentforge.backend.auth.service;

import com.agentforge.backend.auth.dto.*;
import com.agentforge.backend.auth.exception.EmailAlreadyExistsException;
import com.agentforge.backend.auth.exception.InvalidRefreshTokenException;
import com.agentforge.backend.auth.exception.RefreshTokenReuseException;
import com.agentforge.backend.auth.mapper.AuthMapper;
import com.agentforge.backend.common.enums.SystemRole;
import com.agentforge.backend.common.enums.UserStatus;
import com.agentforge.backend.domain.user.RefreshToken;
import com.agentforge.backend.domain.user.RefreshTokenRepository;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.domain.user.UserRepository;
import com.agentforge.backend.security.jwt.JwtProperties;
import com.agentforge.backend.security.jwt.JwtService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.transaction.annotation.Transactional;
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
    private final JwtProperties jwtProperties;
    private final RefreshTokenRepository refreshTokenRepository;
    private final RefreshTokenService refreshTokenService;

    @Override
    public UserResponse register(RegisterRequest request) {

        if (userRepository.existsByEmail(request.getEmail())) {
            throw new EmailAlreadyExistsException(
                    "Email already registered.");
        }

        User user = authMapper.toEntity(request);
        user.setPassword(
                passwordEncoder.encode(request.getPassword()));
        user.setStatus(UserStatus.ACTIVE);
        user.setSystemRole(SystemRole.USER);
        user.setEmailVerified(false);
        User savedUser = userRepository.save(user);

        return authMapper.toUserResponse(savedUser);
    }

    @Transactional
    @Override
    public JwtResponse login(LoginRequest request,
            HttpServletRequest httpRequest) {

        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.email(),
                        request.password()));

        User user = userRepository
                .findByEmail(request.email())
                .orElseThrow();

        String accessToken = jwtService.generateAccessToken(user);

        String refreshToken = jwtService.generateRefreshToken(user);

        String userAgent = httpRequest.getHeader("User-Agent");
        String deviceNameHeader = httpRequest.getHeader("X-Device-Name");
        String deviceTypeHeader = httpRequest.getHeader("X-Device-Type");

        String ipAddress = getClientIpAddress(httpRequest);

        String deviceType = detectDeviceType(userAgent, deviceTypeHeader);

        String deviceName = detectDeviceName(userAgent, deviceNameHeader);

        RefreshToken entity = RefreshToken.builder()
                .token(refreshToken)
                .user(user)
                .expiresAt(
                        LocalDateTime.now()
                                .plusSeconds(
                                        jwtProperties.refreshTokenExpiration()
                                                / 1000))
                .revoked(false)
                .deviceName(deviceName)

                .deviceType(deviceType)

                .userAgent(userAgent)

                .ipAddress(ipAddress)

                .lastUsedAt(LocalDateTime.now())

                .build();

        refreshTokenRepository.save(entity);

        return JwtResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtProperties
                        .accessTokenExpiration()
                        / 1000)
                .build();

    }

    @Override
    @Transactional
    public void logout(LogoutRequest request) {

        refreshTokenService.revokeToken(
                request.refreshToken());
    }

    @Override
    @Transactional
    public void logoutAll(User user) {

        refreshTokenService.revokeAllTokens(user);
    }

    @Override
    @Transactional(noRollbackFor = { RefreshTokenReuseException.class, InvalidRefreshTokenException.class })
    public JwtResponse refresh(
            RefreshTokenRequest request,
            HttpServletRequest httpRequest) {

        String oldToken = request.refreshToken();

        RefreshToken existingToken = refreshTokenService.findValidToken(oldToken);

        if (!jwtService.isTokenValid(oldToken)) {

            existingToken.setRevoked(true);

            refreshTokenRepository.save(existingToken);

            throw new InvalidRefreshTokenException(
                    "Invalid refresh token.");
        }

        String email = jwtService.extractUsername(oldToken);

        User user = existingToken.getUser();

        if (!user.getEmail().equals(email)) {

            existingToken.setRevoked(true);

            refreshTokenRepository.save(existingToken);

            throw new InvalidRefreshTokenException(
                    "Refresh token does not belong to the user.");
        }

        existingToken.setRevoked(true);

        existingToken.setLastUsedAt(
                LocalDateTime.now());

        refreshTokenRepository.save(existingToken);

        String newAccessToken = jwtService.generateAccessToken(user);

        String newRefreshToken = jwtService.generateRefreshToken(user);

        String userAgent = existingToken.getUserAgent();

        String ipAddress = getClientIpAddress(httpRequest);

        String deviceType = existingToken.getDeviceType();

        String deviceName = existingToken.getDeviceName();

        RefreshToken rotatedToken = RefreshToken.builder()

                .token(newRefreshToken)

                .user(user)

                .expiresAt(
                        LocalDateTime.now()
                                .plusSeconds(
                                        jwtProperties
                                                .refreshTokenExpiration()
                                                / 1000))

                .revoked(false)

                .deviceName(deviceName)

                .deviceType(deviceType)

                .userAgent(userAgent)

                .ipAddress(ipAddress)

                .lastUsedAt(
                        LocalDateTime.now())

                .build();

        refreshTokenRepository.save(rotatedToken);

        return JwtResponse.builder()

                .accessToken(newAccessToken)

                .refreshToken(newRefreshToken)

                .tokenType("Bearer")

                .expiresIn(
                        jwtProperties
                                .accessTokenExpiration()
                                / 1000)

                .build();
    }

    private String getClientIpAddress(
            HttpServletRequest request) {

        String forwardedFor = request.getHeader("X-Forwarded-For");

        if (forwardedFor != null
                && !forwardedFor.isBlank()) {

            return forwardedFor
                    .split(",")[0]
                    .trim();
        }

        String realIp = request.getHeader("X-Real-IP");

        if (realIp != null
                && !realIp.isBlank()) {

            return realIp;
        }

        return request.getRemoteAddr();
    }

    private String detectDeviceType(
            String userAgent,
            String headerType) {
        if (headerType != null && !headerType.isBlank()) {
            return headerType.trim().toUpperCase();
        }

        if (userAgent == null || userAgent.isBlank()) {
            return "UNKNOWN";
        }

        String agent = userAgent.toLowerCase();

        if (agent.contains("postman") || agent.contains("insomnia") || agent.contains("curl")
                || agent.contains("swagger")) {
            return "DESKTOP";
        }

        if (agent.contains("mobile") || agent.contains("iphone") || agent.contains("ipod")) {
            return "MOBILE";
        }

        if (agent.contains("ipad") || agent.contains("tablet")) {
            return "TABLET";
        }

        if (agent.contains("android")) {
            return agent.contains("mobile") ? "MOBILE" : "TABLET";
        }

        if (agent.contains("windows") || agent.contains("win64") || agent.contains("win32")
                || agent.contains("mac") || agent.contains("macintosh")
                || agent.contains("linux") || agent.contains("x11") || agent.contains("cros")) {
            return "DESKTOP";
        }

        if (agent.contains("mozilla") || agent.contains("chrome") || agent.contains("safari")
                || agent.contains("firefox") || agent.contains("edge")) {
            return "DESKTOP";
        }

        return "UNKNOWN";
    }

    private String detectDeviceName(
            String userAgent,
            String headerName) {
        if (headerName != null && !headerName.isBlank()) {
            return headerName.trim();
        }

        if (userAgent == null || userAgent.isBlank()) {
            return "Unknown Device";
        }

        String agent = userAgent.toLowerCase();

        if (agent.contains("postman")) {
            return "Postman Client";
        }
        if (agent.contains("insomnia")) {
            return "Insomnia Client";
        }
        if (agent.contains("curl")) {
            return "cURL Client";
        }
        if (agent.contains("swagger")) {
            return "Swagger UI";
        }

        if (agent.contains("iphone")) {
            return "iPhone";
        }
        if (agent.contains("ipad")) {
            return "iPad";
        }
        if (agent.contains("ipod")) {
            return "iPod";
        }
        if (agent.contains("android")) {
            return agent.contains("mobile") ? "Android Phone" : "Android Tablet";
        }
        if (agent.contains("windows") || agent.contains("win64") || agent.contains("win32")) {
            return "Windows PC";
        }
        if (agent.contains("mac") || agent.contains("macintosh")) {
            return "Mac";
        }
        if (agent.contains("cros")) {
            return "Chromebook";
        }
        if (agent.contains("linux") || agent.contains("x11")) {
            return "Linux PC";
        }

        return "Unknown Device";
    }
}
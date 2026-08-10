package com.agentforge.backend.auth.controller;

import com.agentforge.backend.auth.dto.*;
import com.agentforge.backend.auth.service.AuthService;
import com.agentforge.backend.common.response.ApiResponse;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.security.auth.CustomUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import jakarta.servlet.http.HttpServletRequest;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<Void>> register(

            @Valid
            @RequestBody
            RegisterRequest request

    ) {
        UserResponse response = authService.register(request);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                        ApiResponse.<Void>builder()
                                .success(true)
                                .message("User registered successfully.")
                                .data(null)
                                .timestamp(LocalDateTime.now())
                                .build()
                );
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<JwtResponse>> login(
            @Valid
            @RequestBody
            LoginRequest request,
            HttpServletRequest httpRequest
    ) {
        JwtResponse response = authService.login(request, httpRequest);

        return ResponseEntity.ok(
                ApiResponse.<JwtResponse>builder()
                        .success(true)
                        .message("Login successful.")
                        .data(response)
                        .timestamp(LocalDateTime.now())
                        .build()
        );
    }

    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Void>> logout(

            @Valid
            @RequestBody
            LogoutRequest request

    ) {

        authService.logout(request);

        return ResponseEntity.ok(

                ApiResponse.<Void>builder()
                        .success(true)
                        .message("Logged out successfully.")
                        .data(null)
                        .timestamp(LocalDateTime.now())
                        .build()

        );
    }

    @PostMapping("/logout-all")
    public ResponseEntity<ApiResponse<Void>> logoutAll(

            Authentication authentication

    ) {

        if (authentication == null ||
                !authentication.isAuthenticated()) {

            return ResponseEntity
                    .status(HttpStatus.UNAUTHORIZED)
                    .body(
                            ApiResponse.<Void>builder()
                                    .success(false)
                                    .message("Authentication required.")
                                    .data(null)
                                    .timestamp(LocalDateTime.now())
                                    .build()
                    );
        }

        CustomUserDetails userDetails =
                (CustomUserDetails) authentication.getPrincipal();

        User user = userDetails.getUser();

        authService.logoutAll(user);

        return ResponseEntity.ok(

                ApiResponse.<Void>builder()
                        .success(true)
                        .message("Logged out from all devices successfully.")
                        .data(null)
                        .timestamp(LocalDateTime.now())
                        .build()

        );
    }

    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<JwtResponse>> refresh(

            @Valid
            @RequestBody
            RefreshTokenRequest request,

            HttpServletRequest httpRequest

    ) {

        JwtResponse response =
                authService.refresh(
                        request,
                        httpRequest
                );

        return ResponseEntity.ok(

                ApiResponse.<JwtResponse>builder()

                        .success(true)

                        .message(
                                "Token refreshed successfully."
                        )

                        .data(response)

                        .timestamp(
                                LocalDateTime.now()
                        )

                        .build()

        );
    }

}

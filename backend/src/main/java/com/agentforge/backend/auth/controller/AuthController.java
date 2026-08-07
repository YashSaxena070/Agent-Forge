package com.agentforge.backend.auth.controller;

import com.agentforge.backend.auth.dto.RegisterRequest;
import com.agentforge.backend.auth.dto.UserResponse;
import com.agentforge.backend.auth.service.AuthService;
import com.agentforge.backend.common.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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
}

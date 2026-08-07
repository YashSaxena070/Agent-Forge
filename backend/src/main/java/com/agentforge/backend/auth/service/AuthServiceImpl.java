package com.agentforge.backend.auth.service;

import com.agentforge.backend.auth.dto.RegisterRequest;
import com.agentforge.backend.auth.dto.UserResponse;
import com.agentforge.backend.auth.exception.EmailAlreadyExistsException;
import com.agentforge.backend.auth.mapper.AuthMapper;
import com.agentforge.backend.common.enums.SystemRole;
import com.agentforge.backend.common.enums.UserStatus;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.domain.user.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthMapper authMapper;

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
}
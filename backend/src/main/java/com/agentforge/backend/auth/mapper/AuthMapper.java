package com.agentforge.backend.auth.mapper;

import com.agentforge.backend.auth.dto.CurrentUserResponse;
import com.agentforge.backend.auth.dto.RegisterRequest;
import com.agentforge.backend.auth.dto.SessionResponse;
import com.agentforge.backend.auth.dto.UserResponse;
import com.agentforge.backend.domain.user.RefreshToken;
import com.agentforge.backend.domain.user.User;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring", builder = @org.mapstruct.Builder(disableBuilder = true))
public interface AuthMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "password", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "systemRole", ignore = true)
    @Mapping(target = "emailVerified", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    User toEntity(RegisterRequest request);

    UserResponse toUserResponse(User user);

    CurrentUserResponse toCurrentUserResponse(User user);

    @Mapping(target = "current", ignore = true)
    SessionResponse toSessionResponse(RefreshToken refreshToken);

}
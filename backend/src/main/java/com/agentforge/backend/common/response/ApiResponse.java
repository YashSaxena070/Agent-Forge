package com.agentforge.backend.common.response;

import lombok.Builder;

import java.time.LocalDateTime;

@Builder
public record ApiResponse<T>(
        boolean success,

        String message,

        T data,

        LocalDateTime timestamp
) {
}
